import re
from dataclasses import dataclass, field
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import IntegerField, Case, When, Value, Q, Count
from django.forms import SelectMultiple, RadioSelect, formset_factory
from django.utils.translation import gettext_lazy as _
from functools import cached_property
from itertools import chain
from typing import List

from cobalt import FrbrUri
from indigo.tasks import TaskBroker
from indigo_api.models import Work, TaxonomyTopic, Amendment, Subtype, Locality, PublicationDocument, \
    Commencement, Task, Country, WorkAlias, ArbitraryExpressionDate, AllPlace
from indigo_app.forms.mixins import FormAsUrlMixin


def remove_punctuation(value):
    value = re.sub(r'[\s!?@#$§±%^&*;:,.<>(){}\[\]\\/|"\'“”‘’‟„‛‚«»‹›]+', '-', value, flags=re.IGNORECASE)
    value = re.sub(r'--+', '-', value)
    return value


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = (
            'title', 'frbr_uri', 'assent_date', 'parent_work', 'commenced',
            'repealed_by', 'repealed_date', 'publication_name', 'publication_number', 'publication_date',
            'publication_document_trusted_url', 'publication_document_size', 'publication_document_mime_type',
            'stub', 'principal', 'taxonomy_topics', 'as_at_date_override', 'consolidation_note_override', 'country', 'locality',
            'disclaimer',
        )

    # FRBR URI fields
    # this will be filled in automatically during cleaning
    frbr_uri = forms.CharField(required=False)
    # TODO: these should be choice fields and the options restricted to the place
    frbr_doctype = forms.ChoiceField()
    frbr_subtype = forms.ChoiceField(required=False)
    frbr_actor = forms.CharField(required=False)
    # TODO: clean and validate these
    frbr_date = forms.CharField()
    # TODO: clean this up
    frbr_number = forms.CharField()

    # The user can provide either a file attachment, or a trusted
    # remote URL with supporting data. The form sorts out which fields
    # are applicable in each case.
    publication_document_file = forms.FileField(required=False)
    delete_publication_document = forms.BooleanField(required=False)
    taxonomy_topics = forms.ModelMultipleChoiceField(
        queryset=TaxonomyTopic.objects.all(),
        to_field_name='slug', required=False)
    publication_document_trusted_url = forms.URLField(required=False)
    publication_document_size = forms.IntegerField(required=False)
    publication_document_mime_type = forms.CharField(required=False)

    # custom work properties that shouldn't be rendered automatically.
    # this assumes that these properties are rendered manually on the form
    # page.
    no_render_properties = []

    def __init__(self, country, locality, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country = country
        self.locality = locality
        self.place = locality or country
        self.user = user
        self.formsets = []

        for prop, label in self.place.settings.work_properties.items():
            key = f'property_{prop}'
            if self.instance:
                self.initial[key] = self.instance.properties.get(prop)
            self.fields[key] = forms.CharField(label=label, required=False)

        if self.instance:
            self.fields['frbr_doctype'].initial = self.instance.doctype
            self.fields['frbr_subtype'].initial = self.instance.subtype
            self.fields['frbr_date'].initial = self.instance.date
            self.fields['frbr_number'].initial = self.instance.number
            self.fields['frbr_actor'].initial = self.instance.actor

        self.fields['frbr_doctype'].choices = [
            (y, x)
            for (x, y) in settings.INDIGO['DOCTYPES'] + settings.INDIGO['EXTRA_DOCTYPES'].get(self.country.code, [])
        ]
        self.fields['frbr_subtype'].choices = [
            (s.abbreviation, s.name)
            for s in Subtype.objects.order_by('name')
        ]

        self.fields['locality'].queryset = Locality.objects.filter(country=self.country)
        self.create_formsets()

    def create_formsets(self):
        self.aliases_formset = WorkAliasesFormSet(
            self.data if self.is_bound else None,
            work=self.instance,
            form_kwargs={'work': self.instance, 'user': self.user},
            prefix="aliases",
            initial=[{'alias': x.alias} for x in self.instance.aliases.all()] if self.instance and self.instance.pk else []
        )
        self.formsets.append(self.aliases_formset)

        if self.instance.pk:
            # repeal formset
            repeals_made_formset_kwargs = {
                "work": self.instance,
                "user": self.user,
                "form_kwargs": {
                    "work": self.instance,
                    "user": self.user,
                },
                "prefix": "repeals_made",
                "initial": [{
                    "repealed_work": repealed_work,
                    "repealed_date": repealed_work.repealed_date,
                } for repealed_work in self.instance.repealed_works.all()]
            }
            if self.is_bound:
                repeals_made_formset_kwargs["data"] = self.data
            self.repeals_made_formset = RepealMadeBaseFormSet(**repeals_made_formset_kwargs)
            self.formsets.append(self.repeals_made_formset)

            amended_by_formset_kwargs = {
                "work": self.instance,
                "user": self.user,
                "form_kwargs": {
                    "work": self.instance,
                    "user": self.user,
                },
                "prefix": "amended_by",
                "initial": [{
                    "amended_work": self.instance,
                    "amending_work": amendment.amending_work,
                    "date": amendment.date,
                    "id": amendment.id,
                }
                    for amendment in Amendment.objects.filter(amended_work=self.instance)],
            }
            if self.is_bound:
                amended_by_formset_kwargs["data"] = self.data
            self.amended_by_formset = AmendmentsBaseFormSet(**amended_by_formset_kwargs)
            self.formsets.append(self.amended_by_formset)

            amendments_made_formset_kwargs = {
                "work": self.instance,
                "user": self.user,
                "form_kwargs": {
                    "work": self.instance,
                    "user": self.user,
                },
                "prefix": "amendments_made",
                "initial": [{
                    "amended_work": amendment.amended_work,
                    "amending_work": self.instance,
                    "date": amendment.date,
                    "id": amendment.id,
                }
                    for amendment in Amendment.objects.filter(amending_work=self.instance)],
            }
            if self.is_bound:
                amendments_made_formset_kwargs["data"] = self.data
            self.amendments_made_formset = AmendmentsBaseFormSet(**amendments_made_formset_kwargs)
            self.formsets.append(self.amendments_made_formset)

            commencements_formset_kwargs = {
                "work": self.instance,
                "user": self.user,
                "form_kwargs": {
                    "work": self.instance,
                    "user": self.user,
                },
                "prefix": "commencements",
                "initial": [{
                    "commenced_work": self.instance,
                    "commencing_work": commencement.commencing_work,
                    "note": commencement.note,
                    "date": commencement.date,
                    "id": commencement.id,
                }
                    for commencement in self.instance.commencements.all()],
            }

            if self.is_bound:
                commencements_formset_kwargs["data"] = self.data
            self.commencements_formset = CommencementsBaseFormset(**commencements_formset_kwargs)
            self.formsets.append(self.commencements_formset)

            commencements_made_formset_kwargs = {
                "work": self.instance,
                "user": self.user,
                "form_kwargs": {
                    "work": self.instance,
                    "user": self.user,
                },
                "prefix": "commencements_made",
                "initial": [{
                    "commenced_work": commencement.commenced_work,
                    "commencing_work": self.instance,
                    "note": commencement.note,
                    "date": commencement.date,
                    "id": commencement.id,
                }
                    for commencement in Commencement.objects.filter(commencing_work=self.instance)],
            }

            if self.is_bound:
                commencements_made_formset_kwargs["data"] = self.data
            self.commencements_made_formset = CommencementsMadeBaseFormset(**commencements_made_formset_kwargs)
            self.formsets.append(self.commencements_made_formset)

            consolidation_formset_kwargs = {
                "work": self.instance,
                "user": self.user,
                "form_kwargs": {
                    "work": self.instance,
                    "user": self.user,
                },
                "prefix": "consolidations",
                "initial": [{
                    "date": consolidation.date,
                    "id": consolidation.id,
                } for consolidation in ArbitraryExpressionDate.objects.filter(work=self.instance)]
            }
            if self.is_bound:
                consolidation_formset_kwargs["data"] = self.data
            self.consolidations_formset = ConsolidationsBaseFormset(**consolidation_formset_kwargs)
            self.formsets.append(self.consolidations_formset)

        self.fields['frbr_doctype'].choices = [
            (y, x)
            for (x, y) in settings.INDIGO['DOCTYPES'] + settings.INDIGO['EXTRA_DOCTYPES'].get(self.country.code, [])
        ]
        self.fields['frbr_subtype'].choices = [
            (s.abbreviation, s.name)
            for s in Subtype.objects.order_by('name')
        ]

        self.fields['locality'].queryset = Locality.objects.filter(country=self.country)

    def property_fields(self):
        fields = [
            self[f'property_{prop}']
            for prop in self.place.settings.work_properties.keys()
            if prop not in self.no_render_properties
        ]
        fields.sort(key=lambda f: f.label)
        return fields

    def is_valid(self):
        # all returns True if formsets is empty
        return super().is_valid() and all(formset.is_valid() for formset in self.formsets)

    def has_changed(self):
        # any returns False if formsets is empty
        return super().has_changed() or any(formset.has_changed() for formset in self.formsets)

    def clean_frbr_number(self):
        return remove_punctuation(self.cleaned_data['frbr_number'])

    def clean_frbr_actor(self):
        return remove_punctuation(self.cleaned_data['frbr_actor'])

    def clean(self):
        cleaned_data = super().clean()

        # build up the FRBR URI from its constituent parts
        # TODO: this should really be done on the model itself, so that we can store and query the FRBR URI fields independently
        try:
            frbr_uri = FrbrUri(
                self.place.place_code, None, cleaned_data['frbr_doctype'], cleaned_data.get('frbr_subtype'),
                cleaned_data.get('frbr_actor'), cleaned_data.get('frbr_date'), cleaned_data.get('frbr_number'))
            self.cleaned_data['frbr_uri'] = frbr_uri.work_uri(work_component=False)
        except (TypeError, ValueError) as e:
            raise ValidationError(_("Error building FRBR URI"))

        return self.cleaned_data

    def save(self, commit=True):
        work = super().save(commit)
        self.save_properties()
        self.save_publication_document()
        self.save_formsets()
        return work

    def save_properties(self):
        for prop in self.place.settings.work_properties.keys():
            val = self.cleaned_data.get(f'property_{prop}')
            if val is not None and val != '':
                self.instance.properties[prop] = val
            elif prop in self.instance.properties:
                # a work property has been removed
                del self.instance.properties[prop]
        self.instance.save()

    def save_formsets(self):
        for formset in self.formsets:
            formset.save()

    def save_publication_document(self):
        pub_doc_file = self.cleaned_data['publication_document_file']
        pub_doc_url = self.cleaned_data['publication_document_trusted_url']

        try:
            existing = self.instance.publication_document
        except PublicationDocument.DoesNotExist:
            existing = None

        if self.cleaned_data['delete_publication_document']:
            if existing:
                existing.delete()
                existing = None

        if pub_doc_file:
            if existing:
                # ensure any previously uploaded file is deleted
                existing.delete()

            pub_doc = PublicationDocument(work=self.instance)
            pub_doc.trusted_url = None
            pub_doc.file = pub_doc_file
            pub_doc.size = pub_doc_file.size
            pub_doc.mime_type = pub_doc_file.content_type
            pub_doc.save()

        elif pub_doc_url:
            if existing:
                # ensure any previously uploaded file is deleted
                existing.delete()

            pub_doc = PublicationDocument(work=self.instance)
            pub_doc.file = None
            pub_doc.trusted_url = pub_doc_url
            pub_doc.size = self.cleaned_data['publication_document_size']
            pub_doc.mime_type = self.cleaned_data['publication_document_mime_type']
            pub_doc.save()

    @cached_property
    def taxonomy_toc(self):
        return TaxonomyTopic.get_toc_tree()


class BasePartialWorkFormSet(forms.BaseFormSet):
    def __init__(self, *args, work=None, user=None, **kwargs):
        self.work = work
        self.user = user
        super().__init__(*args, **kwargs)


    def save(self):
        for form in self.forms:
            if form.has_changed():
                form.save()


class BasePartialWorkForm(forms.Form):
    def __init__(self, *args, work, user,  **kwargs):
        super().__init__(*args, **kwargs)
        self.work = work
        self.user = user


class WorkAliasForm(BasePartialWorkForm):
    alias = forms.CharField(label=_('Alias'), max_length=1024, required=False)

    def save(self, *args, **kwargs):
        pass


WorkAliasesBaseFormSet = formset_factory(
    WorkAliasForm,
    extra=2,
    formset=BasePartialWorkFormSet,
)


class WorkAliasesFormSet(WorkAliasesBaseFormSet):
    def save(self, *args, **kwargs):
        existing = [x.alias for x in self.work.aliases.all()]
        new = [form.cleaned_data['alias'] for form in self.forms if form.cleaned_data.get('alias')]
        if existing != new:
            for alias in self.work.aliases.all():
                if alias.alias not in new:
                    alias.delete()
            for alias in new:
                if alias not in existing:
                    WorkAlias.objects.create(work=self.work, alias=alias)


class AmendmentForm(BasePartialWorkForm):
    amending_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    amended_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    @cached_property
    def amending_work_obj(self):
        return Work.objects.filter(pk=self['amending_work'].value()).first()

    @cached_property
    def amended_work_obj(self):
        return Work.objects.filter(pk=self['amended_work'].value()).first()

    def save(self, *args, **kwargs):
        amendment = Amendment.objects.filter(pk=self.cleaned_data['id']).first()

        if self.cleaned_data.get('DELETE'):
            if amendment:
                amendment.delete()
            return
        else:
            if amendment:
                amendment.amending_work = self.cleaned_data['amending_work']
                amendment.amended_work = self.cleaned_data['amended_work']
                amendment.date = self.cleaned_data["date"]
                amendment.updated_by_user = self.user
                amendment.save()
                # update documents and tasks
                amendment.update_date_for_related(old_date=self.initial['date'])
            else:
                Amendment.objects.create(
                    amended_work=self.cleaned_data['amended_work'],
                    amending_work=self.cleaned_data['amending_work'],
                    date=self.cleaned_data["date"],
                    created_by_user=self.user,
                    updated_by_user=self.user,
                )


AmendmentsFormSet = formset_factory(
    AmendmentForm,
    extra=0,
    can_delete=True,
    formset=BasePartialWorkFormSet,
)


class AmendmentsBaseFormSet(AmendmentsFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        # check if amending work and date are unique together
        seen = set()
        for form in self.forms:
            if form.cleaned_data.get('DELETE'):
                continue
            amending_work = form.cleaned_data.get('amending_work')
            amended_work = form.cleaned_data.get('amended_work')
            date = form.cleaned_data.get('date')
            if (amending_work, amended_work, date) in seen:
                raise ValidationError(_("Amending work and date must be unique together."))
            seen.add((amending_work, amended_work, date))


class RepealMadeForm(BasePartialWorkForm):
    repealed_work = forms.ModelChoiceField(queryset=Work.objects)
    repealed_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    @cached_property
    def repealed_work_obj(self):
        return Work.objects.filter(pk=self['repealed_work'].value()).first()

    def is_repealed_work_saved(self):
        return self.repealed_work_obj.repealed_by == self.work

    def save(self, *args, **kwargs):
        work = self.cleaned_data['repealed_work']
        if self.cleaned_data.get('DELETE'):
            if work.repealed_by == self.work:
                work.repealed_by = None
                work.repealed_date = None
                work.save_with_revision(user=self.user)
        else:
            work.repealed_by = self.work
            work.repealed_date = self.cleaned_data['repealed_date']
            work.save_with_revision(user=self.user)


RepealMadeFormSet = formset_factory(
    RepealMadeForm,
    extra=0,
    can_delete=True,
    formset=BasePartialWorkFormSet,
)


class RepealMadeBaseFormSet(RepealMadeFormSet):
    pass


class ConsolidationForm(BasePartialWorkForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def save(self, *args, **kwargs):
        consolidation = ArbitraryExpressionDate.objects.filter(pk=self.cleaned_data['id']).first()

        if self.cleaned_data.get('DELETE'):
            if consolidation:
                consolidation.delete()
            return
        else:
            if consolidation:
                consolidation.date = self.cleaned_data["date"]
                consolidation.updated_by_user = self.user
                consolidation.save()
            else:
                ArbitraryExpressionDate.objects.create(
                    work=self.work,
                    date=self.cleaned_data["date"],
                    created_by_user=self.user,
                    updated_by_user=self.user,
                )


ConsolidationsFormSet = formset_factory(
    ConsolidationForm,
    extra=0,
    can_delete=True,
    formset=BasePartialWorkFormSet
)


class ConsolidationsBaseFormset(ConsolidationsFormSet):
    def clean(self):
        seen = set()
        for form in self.forms:
            if form.cleaned_data.get('DELETE'):
                continue
            date = form.cleaned_data.get('date')
            if date in seen:
                raise ValidationError(_("Consolidation dates must be unique."))
            seen.add(date)


class FindPubDocForm(forms.Form):
    name = forms.CharField(required=False, widget=forms.HiddenInput())
    trusted_url = forms.URLField(required=False, widget=forms.HiddenInput())
    size = forms.IntegerField(required=False, widget=forms.HiddenInput())
    mimetype = forms.CharField(required=False, widget=forms.HiddenInput())


class CommencementForm(forms.ModelForm):
    provisions = forms.MultipleChoiceField(required=False)
    provisions_select_all = forms.BooleanField(required=False)
    commencing_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    clear_commencing_work = forms.BooleanField(required=False)

    class Meta:
        model = Commencement
        fields = ('date', 'all_provisions', 'provisions', 'main', 'note', 'commencing_work')

    def __init__(self, work, *args, provisions=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.work = work
        self.provisions = provisions or []
        self.fields['provisions'].choices = [(p.id, p.title) for p in self.provisions]

    def clean_main(self):
        if self.cleaned_data['main']:
            # there can be only one!
            qs = Commencement.objects.filter(commenced_work=self.work, main=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_("A main commencement already exists."))
        return self.cleaned_data['main']

    def clean_all_provisions(self):
        if self.cleaned_data['all_provisions']:
            # there can be only one!
            qs = Commencement.objects.filter(commenced_work=self.work)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_("A commencement for all provisions must be the only commencement."))
        return self.cleaned_data['all_provisions']

    def clean(self):
        cleaned_data = super().clean()
        # all_provisions may have been nuked during clean
        if cleaned_data.get('all_provisions') and cleaned_data['provisions']:
            raise ValidationError(_("Cannot specify all provisions, and a list of provisions."))

        # don't try to save a duplicate commencement, we'll get an IntegrityError
        if self.work.commencements.exclude(pk=self.instance.pk).filter(
            commencing_work=cleaned_data.get('commencing_work'),
            date=cleaned_data.get('date')
        ).exists():
            raise ValidationError(_("A commencement at this date and with this commencing work already exists."))

        return cleaned_data


class CommencementsPartialForm(BasePartialWorkForm):
    commencing_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    commenced_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    note = forms.CharField(required=False, widget=forms.TextInput)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    clear_commencing_work = forms.BooleanField(required=False)

    @cached_property
    def commencing_work_obj(self):
        if self['commencing_work'].value():
            return Work.objects.filter(pk=self['commencing_work'].value()).first()

    @cached_property
    def commenced_work_obj(self):
        return Work.objects.filter(pk=self['commenced_work'].value()).first()

    def save(self, *args, **kwargs):
        commencement = Commencement.objects.filter(pk=self.cleaned_data['id']).first()

        if self.cleaned_data.get('DELETE'):
            if commencement:
                commencement.delete()
            return
        else:
            if commencement:
                commencement.commencing_work = self.cleaned_data['commencing_work']
                commencement.commenced_work = self.cleaned_data['commenced_work']
                commencement.date = self.cleaned_data["date"]
                commencement.note = self.cleaned_data["note"]
                commencement.updated_by_user = self.user
                commencement.save()
            else:
                Commencement.objects.create(
                    commencing_work=self.cleaned_data['commencing_work'],
                    commenced_work=self.cleaned_data['commenced_work'],
                    date=self.cleaned_data["date"],
                    note=self.cleaned_data["note"],
                    created_by_user=self.user,
                    updated_by_user=self.user,
                )


CommencementsFormset = formset_factory(
    CommencementsPartialForm,
    extra=0,
    can_delete=True,
    formset=BasePartialWorkFormSet,
)


class CommencementsBaseFormset(CommencementsFormset):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        if self.forms:
            # check if the commencements in the form and the commencements on the work are still in sync
            commencement_ids = {form.cleaned_data.get('id') for form in self.forms if form.cleaned_data.get('id')}
            # same commenced_work for all forms in the formset
            commenced_work = self.forms[0].cleaned_data['commenced_work']
            existing_commencement_ids = {c.pk for c in commenced_work.commencements.all()}
            if commencement_ids != existing_commencement_ids:
                raise ValidationError(_("It seems that commencements have been edited elsewhere. Cancel your edits and make them again."))

        # check if commencing work and date are unique together
        seen = set()
        for form in self.forms:
            if form.cleaned_data.get('DELETE'):
                continue
            commencing_work = form.cleaned_data.get('commencing_work')
            commenced_work = form.cleaned_data.get('commenced_work')
            date = form.cleaned_data.get('date')
            if (commencing_work, commenced_work, date) in seen:
                raise ValidationError(_("Commencing work and date must be unique together."))
            seen.add((commencing_work, commenced_work, date))

    def save(self, *args, **kwargs):
        if self.is_valid() and self.has_changed():
            super().save(*args, **kwargs)
            # some commencements may have been deleted during super save
            self.work.refresh_from_db()

            n_commencements = self.work.commencements.count()
            if n_commencements > 1:
                for c in self.work.commencements.all():
                    if c.all_provisions:
                        c.all_provisions = False
                        c.save()
            elif n_commencements == 1:
                only_commencement = self.work.commencements.first()
                only_commencement.main = True
                only_commencement.all_provisions = True
                only_commencement.save()
            has_main_commencement = bool(self.work.main_commencement)
            if not has_main_commencement:
                # update the first commencement to be the main one, if there is one
                first = self.work.commencements.first()
                if first:
                    first.main = True
                    first.save()


class CommencementsMadeBaseFormset(CommencementsFormset):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        if self.forms:
            # check if the commencements made in the form and the commencements made on the work are still in sync
            commencement_made_ids = {form.cleaned_data.get('id') for form in self.forms if form.cleaned_data.get('id')}
            # same commencing_work for all forms in the formset
            commencing_work = self.forms[0].cleaned_data['commencing_work']
            existing_commencement_made_ids = {c.pk for c in commencing_work.commencements_made.all()}
            if commencement_made_ids != existing_commencement_made_ids:
                raise ValidationError(_("It seems that commencements have been edited elsewhere. Cancel your edits and make them again."))
        # check if commencing work and date are unique together
        seen = set()
        for form in self.forms:
            if form.cleaned_data.get('DELETE'):
                continue
            commencing_work = form.cleaned_data.get('commencing_work')
            commenced_work = form.cleaned_data.get('commenced_work')
            date = form.cleaned_data.get('date')
            if (commencing_work, commenced_work, date) in seen:
                raise ValidationError(_("Commenced work, commencing work, and date must be unique together."))
            seen.add((commencing_work, commenced_work, date))

    def save(self, *args, **kwargs):
        if self.is_valid() and self.has_changed():
            super().save(*args, **kwargs)

            commenced_counts = Commencement.objects.filter(commencing_work=self.work).values("commenced_work").annotate(num_commencements=Count("id")).order_by()
            multiple_commencements = commenced_counts.filter(num_commencements__gt=1).values_list("commenced_work", flat=True)
            single_commencements = commenced_counts.filter(num_commencements=1).values_list("commenced_work", flat=True)

            for commencement in multiple_commencements:
                commencements = Commencement.objects.filter(commencing_work=self.work, commenced_work=commencement).order_by("date")
                all_commencements = Commencement.objects.filter(commenced_work=commencement)

                # update all commencements first
                for c in all_commencements:
                    c.all_provisions = False
                    c.save()

                has_main_commencement = all_commencements.filter(main=True).exists()
                if not has_main_commencement:
                    # update the first commencement to be the main one
                    first = commencements.first()
                    first.main = True
                    first.save()

            for commencement in single_commencements:
                existing_commencements = Commencement.objects.filter(commenced_work=commencement).exclude(commencing_work=self.work)
                c = Commencement.objects.filter(commencing_work=self.work, commenced_work=commencement).first()

                if not existing_commencements:
                    c.main = True
                    c.all_provisions = True
                    c.save()
                else:
                    for existing in existing_commencements:
                        existing.all_provisions = False
                        existing.save()
                    has_main_commencement = existing_commencements.filter(main=True).exists()
                    if not has_main_commencement:
                        # update the first commencement to be the main one
                        c.main = True
                        c.save()


@dataclass
class FacetItem:
    label: str
    value: str
    count: int
    selected: bool
    icon: str = ''
    negated: bool = False


@dataclass
class Facet:
    label: str
    name: str
    type: str
    items: List[FacetItem] = field(default_factory=list)


class PermissiveMultipleChoiceField(forms.MultipleChoiceField):
    def valid_value(self, value):
        # Override this method to skip choice validation and accept any input.
        return True


class NegatableModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """A model choice field that allows mixing of positive and negative options, by prefixing
    the fields with a '-' for negative options. The cleaned data is a tuple of (inclusives, exclusives)."""

    def clean(self, value):
        includes = [v for v in value if not v.startswith('-')]
        excludes = [v[1:] for v in value if v.startswith('-')]

        if includes:
            includes = super().clean(includes)
        if excludes:
            excludes = super().clean(excludes)

        return includes, excludes


class WorkFilterForm(forms.Form, FormAsUrlMixin):
    q = forms.CharField()

    place = forms.MultipleChoiceField()

    assent_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    assent_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    publication_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    publication_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    amendment = forms.MultipleChoiceField(label=_("Amendments"), choices=[('no', 'Not amended'), ('yes', 'Amended')])
    amendment_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    amendment_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    commencement = forms.MultipleChoiceField(label=_("Commencement"), choices=[
        ('no', _('Not commenced')), ('date_unknown', _('Commencement date unknown')), ('yes', _('Commenced')),
        ('partial', _('Partially commenced')), ('multiple', _('Multiple commencements'))
    ])
    commencement_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    commencement_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    repeal = forms.MultipleChoiceField(label=_("Repeals"), choices=[('no', _('Not repealed')), ('yes', _('Repealed'))])
    repealed_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    repealed_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    subtype = forms.MultipleChoiceField(label=_("Type"), choices=[])
    stub = forms.MultipleChoiceField(label=_("Stubs"), choices=[('stub', _('Stub')), ('not_stub', _('Not a stub'))])
    work_in_progress = forms.MultipleChoiceField(label=_("Work in progress"), choices=[
        ('work_in_progress', _('Work in progress')), ('approved', _('Approved'))
    ])
    status = forms.MultipleChoiceField(label=_("Point in time status"), choices=[
        ('published', _('Published')), ('draft', _('Draft'))
    ])
    # add the choices separately as we manually include the opposite of each option
    sortby = forms.ChoiceField()
    principal = forms.MultipleChoiceField(label=_("Principal"), required=False, choices=[
        ('principal', _('Principal')), ('not_principal', _('Not Principal'))
    ])
    tasks = forms.MultipleChoiceField(label=_("Tasks"), required=False, choices=[
        ('has_open_tasks', _('Has open tasks')), ('has_unblocked_tasks', _('Has unblocked tasks')),
        ('has_only_blocked_tasks', _('Has only blocked tasks')), ('no_open_tasks', _('Has no open tasks'))
    ])
    primary = forms.MultipleChoiceField(label=_("Primary and subsidiary"), required=False, choices=[
        ('primary', _('Primary')), ('subsidiary', _('Subsidiary'))
    ])
    consolidation = forms.MultipleChoiceField(label=_("Consolidations"), required=False, choices=[
        ('has_consolidation', _('Has consolidation')), ('no_consolidation', _('No consolidation'))
    ])
    publication_document = forms.MultipleChoiceField(label=_("Publication document"), required=False, choices=[
        ('has_publication_document', _('Has publication document')),
        ('no_publication_document', _('No publication document')),
    ])
    documents = forms.MultipleChoiceField(label=_("Points in time"), required=False, choices=[
        ('one', _('Has one point in time')), ('multiple', _('Has multiple points in time')),
        ('none', _('Has no points in time'))
    ])
    taxonomy_topic = forms.ModelMultipleChoiceField(queryset=TaxonomyTopic.objects, to_field_name='slug', required=False)
    frbr_uris = forms.CharField(required=False)
    frbr_date = PermissiveMultipleChoiceField(label=_("Date"), required=False)

    advanced_filters = ['assent_date_start', 'publication_date_start', 'repealed_date_start', 'amendment_date_start', 'commencement_date_start', 'frbr_uris']

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super().__init__(*args, **kwargs)

        self.add_subtypes()
        self.fields['place'].choices = [
            (c.code, c.name) for c in Country.objects.all()
        ] + [
            (loc.place_code, loc.name) for loc in Locality.objects.all()
        ]
        # ensure all choice fields have negated choices
        self.add_negated_choices()
        # add these choices after adding negations, as we manually include the opposite of each option
        self.add_sortby_choices()

    def add_subtypes(self):
        if not self.country or self.country.code == 'all':
            # doctypes for all countries
            country_doctypes = list(chain(*settings.INDIGO['EXTRA_DOCTYPES'].values()))
        else:
            country_doctypes = settings.INDIGO['EXTRA_DOCTYPES'].get(self.country.code, [])
        doctypes = [(d[1].lower(), d[0]) for d in settings.INDIGO['DOCTYPES'] + country_doctypes]

        subtypes = [(s.abbreviation, s.name) for s in Subtype.objects.all()]
        self.fields['subtype'].choices = doctypes + subtypes
        self.subtypes = Subtype.objects.all()

    def add_sortby_choices(self):
        self.fields['sortby'].choices = [
            ('-created_at', _('Created at (newest first)')), ('created_at', _('Created at (oldest first)')),
            ('-updated_at', _('Updated at (newest first)')), ('updated_at', _('Updated at (oldest first)')),
            ('-date', _('Date (newest first)')), ('date', _('Date (oldest first)')),
            ('title', _('Title (A-Z)')), ('-title', _('Title (Z-A)')),
            ('number', _('Number (ascending)')), ('-number', _('Number (descending)')),
        ]

    def add_negated_choices(self):
        for fld in self.fields.values():
            choices = getattr(fld, 'choices', None)
            if choices is not None and isinstance(choices, (list, tuple)):
                fld.choices = fld.choices + [(f"-{value}", label) for value, label in fld.choices]

    def show_advanced_filters(self):
        # Should we show the advanced options box by default?
        # true if there is a value set, and it's not the initial value
        def is_set(a):
            return (self.cleaned_data.get(a) and
                    (not self.fields.get(a).initial or
                     self.fields.get(a).initial != self.cleaned_data.get(a)))

        return any(is_set(a) for a in self.advanced_filters)

    def filter_queryset(self, queryset, exclude=None):
        if self.cleaned_data.get('q'):
            queryset = queryset.filter(Q(title__icontains=self.cleaned_data['q']) | Q(frbr_uri__icontains=self.cleaned_data['q']))

        if self.cleaned_data.get('frbr_uris'):
            # filter by *work* FRBR URI
            uris = []
            for s in self.cleaned_data['frbr_uris'].split():
                try:
                    frbr_uri = FrbrUri.parse(s)
                    uris.append(frbr_uri.work_uri(work_component=False))
                except ValueError:
                    continue
            if uris:
                queryset = queryset.filter(frbr_uri__in=uris)

        if exclude != "place":
            q = Q()
            for place in self.cleaned_data.get('place', []):
                country, locality = Country.get_country_locality(place)
                q |= Q(country=country, locality=locality)
            queryset = queryset.filter(q)

        if exclude != "frbr_date":
            if self.cleaned_data.get('frbr_date'):
                queryset = self.apply_values_filter(self.cleaned_data["frbr_date"], queryset, "date")

        # filter by work in progress
        if exclude != "work_in_progress":
            queryset = self.apply_options_filter(self.cleaned_data.get("work_in_progress", []), queryset, {
                "work_in_progress": Q(work_in_progress=True),
                "approved": Q(work_in_progress=False),
            })

        # filter by stub
        if exclude != "stub":
            queryset = self.apply_options_filter(self.cleaned_data.get("stub", []), queryset, {
                "stub": Q(stub=True),
                "not_stub": Q(stub=False),
            })

        # filter by principal
        if exclude != "principal":
            queryset = self.apply_options_filter(self.cleaned_data.get("principal", []), queryset, {
                "principal": Q(principal=True),
                "not_principal": Q(principal=False),
            })

        # filter by tasks status
        if exclude != "tasks":
            queryset = self.apply_options_filter(self.cleaned_data.get("tasks", []), queryset, {
                "has_open_tasks": Q(id__in=queryset.filter(tasks__state__in=Task.OPEN_STATES).values_list('pk', flat=True)),
                "has_unblocked_tasks": Q(id__in=queryset.filter(tasks__state__in=Task.UNBLOCKED_STATES).values_list('pk', flat=True)),
                "has_only_blocked_tasks": Q(id__in=queryset.filter(tasks__state=Task.BLOCKED).exclude(tasks__state__in=Task.UNBLOCKED_STATES).values_list('pk', flat=True)),
                "no_open_tasks": Q(id__in=queryset.exclude(tasks__state__in=Task.OPEN_STATES).values_list('pk', flat=True)),
            })

        # filter by primary or subsidiary work
        if exclude != "primary":
            queryset = self.apply_options_filter(self.cleaned_data.get('primary', []), queryset, {
                "primary": Q(parent_work__isnull=True),
                "subsidiary": Q(parent_work__isnull=False),
            })

        # doctype, subtype
        if exclude != "subtype":
            # differentiate between subtypes and doctypes
            values = self.cleaned_data.get('subtype', [])
            includes = self.get_doctype_subtype_filter([v for v in values if not v.startswith("-")])
            excludes = self.get_doctype_subtype_filter([v[1:] for v in values if v.startswith("-")])
            if includes.children:
                queryset = queryset.filter(includes)
            if excludes.children:
                queryset = queryset.exclude(excludes)

        # filter by assent date range
        if self.cleaned_data.get('assent_date_start') and self.cleaned_data.get('assent_date_end'):
            start_date = self.cleaned_data['assent_date_start']
            end_date = self.cleaned_data['assent_date_end']
            queryset = queryset.filter(assent_date__range=[start_date, end_date]).order_by('-assent_date')

        # filter by publication date
        if self.cleaned_data.get('publication_date_start') and self.cleaned_data.get('publication_date_end'):
            start_date = self.cleaned_data['publication_date_start']
            end_date = self.cleaned_data['publication_date_end']
            queryset = queryset.filter(publication_date__range=[start_date, end_date]).order_by('-publication_date')

        # filter by repeal
        if exclude != "repeal":
            queryset = self.apply_options_filter(self.cleaned_data.get("repeal", []), queryset, {
                "yes": Q(repealed_date__isnull=False),
                "no": Q(repealed_date__isnull=True),
            })

        if self.cleaned_data.get('repealed_date_start') and self.cleaned_data.get('repealed_date_end'):
            start_date = self.cleaned_data['repealed_date_start']
            end_date = self.cleaned_data['repealed_date_end']
            queryset = queryset.filter(repealed_date__range=[start_date, end_date]).order_by('-repealed_date')

        # filter by amendment
        if exclude != "amendment":
            queryset = self.apply_options_filter(self.cleaned_data.get("amendment", []), queryset, {
                "yes": Q(amendments__date__isnull=False),
                "no": Q(amendments__date__isnull=True),
            })

        if self.cleaned_data.get('amendment_date_start') and self.cleaned_data.get('amendment_date_end'):
            start_date = self.cleaned_data['amendment_date_start']
            end_date = self.cleaned_data['amendment_date_end']
            queryset = queryset.filter(amendments__date__range=[start_date, end_date]).order_by('-amendments__date')

        # filter by commencement status
        if exclude != "commencement":
            queryset = queryset.annotate(Count("commencements"))
            queryset = self.apply_options_filter(self.cleaned_data.get("commencement", []), queryset, {
                "yes": Q(commenced=True),
                "no": Q(commenced=False),
                "date_unknown": Q(commencements__date__isnull=True, commenced=True),
                "multiple": Q(commencements__count__gt=1),
            })

        if self.cleaned_data.get('commencement_date_start') and self.cleaned_data.get('commencement_date_end'):
            start_date = self.cleaned_data['commencement_date_start']
            end_date = self.cleaned_data['commencement_date_end']
            queryset = queryset.filter(commencements__date__range=[start_date, end_date]).order_by('-commencements__date')

        # filter by consolidation
        if exclude != "consolidation":
            queryset = self.apply_options_filter(self.cleaned_data.get("consolidation", []), queryset, {
                "has_consolidation": Q(arbitrary_expression_dates__date__isnull=False),
                "no_consolidation": Q(arbitrary_expression_dates__date__isnull=True),
            })

        # filter by publication document
        if exclude != "publication_document":
            queryset = self.apply_options_filter(self.cleaned_data.get("publication_document", []), queryset, {
                "has_publication_document": Q(publication_document__isnull=False),
                "no_publication_document": Q(publication_document__isnull=True),
            })

        # filter by points in time
        if exclude != "documents":
            queryset = self.apply_options_filter(self.cleaned_data.get('documents', []), queryset, {
                "one": Q(id__in=queryset.filter(document__deleted=False).annotate(Count('document')).filter(document__count=1).values_list('pk', flat=True)),
                "multiple": Q(id__in=queryset.filter(document__deleted=False).annotate(Count('document')).filter(document__count__gt=1).values_list('pk', flat=True)),
                "none": (
                    # either there are no documents at all
                    Q(document__isnull=True) |
                    # or they're all deleted
                    Q(id__in=queryset
                      .filter(document__deleted=True).values_list('pk', flat=True)
                      .exclude(id__in=queryset.filter(document__deleted=False).values_list('pk', flat=True))
                      )
                )
            })

        # filter by point in time status
        if exclude != "status":
            queryset = self.apply_options_filter(self.cleaned_data.get("status", []), queryset, {
                "draft": Q(document__draft=True),
                "published": Q(document__draft=False),
            })

        # filter by taxonomy topic
        if exclude != "taxonomy_topic":
            if self.cleaned_data.get('taxonomy_topic'):
                queryset = queryset.filter(taxonomy_topics__in=self.cleaned_data['taxonomy_topic'])

        # sort by
        if self.cleaned_data.get('sortby'):
            queryset = queryset.order_by(self.cleaned_data.get('sortby'))

        return queryset.distinct()

    def apply_options_filter(self, values, queryset, filters):
        """Apply filters to queryset based on possible values."""
        include_qs = Q()
        exclude_qs = Q()

        for value in values:
            negated = False
            if value.startswith('-'):
                negated = True
                value = value[1:]

            if value in filters:
                if negated:
                    exclude_qs |= Q(filters[value])
                else:
                    include_qs |= Q(filters[value])

        if include_qs.children:
            queryset = queryset.filter(include_qs)

        if exclude_qs.children:
            queryset = queryset.exclude(exclude_qs)

        return queryset

    def apply_values_filter(self, values, queryset, field):
        """Apply filters to a queryset with option values than can be negated."""
        includes = [x for x in values if not x.startswith('-')]
        excludes = [x[1:] for x in values if x.startswith('-')]
        if includes:
            queryset = queryset.filter(**{f"{field}__in": includes})
        if excludes:
            queryset = queryset.exclude(**{f"{field}__in": excludes})
        return queryset

    def apply_model_choices_filter(self, values, queryset, field):
        """Apply filters to a queryset from a field using negatable model choices."""
        includes, excludes = values
        if includes:
            queryset = queryset.filter(**{f"{field}__in": includes})
        if excludes:
            queryset = queryset.exclude(**{f"{field}__in": excludes})
        return queryset

    def get_doctype_subtype_filter(self, values):
        """Get a Q object for filtering by doctype and subtype from the combined options."""
        subtypes = [x.abbreviation for x in self.subtypes]
        subtypes = [v for v in values if v in subtypes]
        doctypes = [v for v in values if v not in subtypes]
        q = Q()

        if subtypes:
            q |= Q(subtype__in=subtypes)

        if doctypes:
            q |= Q(doctype__in=doctypes, subtype=None)

        return q

    def facet_item(self, field, value, count):
        try:
            # what's the label for this value?
            label = next(lab for (val, lab) in self.fields[field].choices if val == value)
        except StopIteration:
            # technically the value is not in the choices, but we can still use it
            label = value

        # is it selected?
        selected = False
        negated = False
        field_obj = self.fields[field]
        if hasattr(field_obj, "queryset"):
            # model choice field
            if isinstance(field_obj, NegatableModelMultipleChoiceField):
                # model choice field that supports negation
                includes, excludes = self.cleaned_data[field]
                if value in [field_obj.prepare_value(v) for v in includes]:
                    selected = True
                elif value in [field_obj.prepare_value(v) for v in excludes]:
                    selected = negated = True
            else:
                selected = value in [field_obj.prepare_value(v) for v in self.cleaned_data.get(field, [])]
        else:
            selected = value in self.cleaned_data.get(field, [])
            if not selected:
                # check if it's negated
                negated = selected = f'-{value}' in self.cleaned_data.get(field, [])

        if negated:
            value = f'-{value}'

        return FacetItem(label, value, count, selected, negated=negated)

    def facet(self, name, type, items):
        items = [self.facet_item(name, value, count) for value, count in items]
        return Facet(self.fields[name].label, name, type, items)

    def work_facets(self, queryset, taxonomy_toc, places_toc):
        work_facets = []
        self.facet_subtype(work_facets, queryset)
        self.facet_principal(work_facets, queryset)
        self.facet_stub(work_facets, queryset)
        self.facet_primary(work_facets, queryset)
        self.facet_frbr_date(work_facets, queryset)
        self.facet_commencement(work_facets, queryset)
        self.facet_amendment(work_facets, queryset)
        self.facet_consolidation(work_facets, queryset)
        self.facet_repeal(work_facets, queryset)
        self.facet_publication_document(work_facets, queryset)
        self.facet_work_in_progress(work_facets, queryset)
        self.facet_tasks(work_facets, queryset)
        self.facet_taxonomy(taxonomy_toc, queryset)
        self.facet_place(places_toc, queryset)
        return work_facets

    def document_facets(self, queryset):
        doc_facets = []
        self.facet_points_in_time(doc_facets, queryset)
        self.facet_point_in_time_status(doc_facets, queryset)
        return doc_facets

    def facet_frbr_date(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="frbr_date")
        counts = {c["date"]: c["count"] for c in qs.values("date").annotate(count=Count("date")).order_by()}
        # inject the choices into the form field
        counts = sorted(counts.items(), key=lambda x: x[0], reverse=True)
        self.fields["frbr_date"].choices = [(d, d) for d, c in counts] + [(f'-{d}', d) for d, c in counts]
        facets.append(self.facet("frbr_date", "checkbox", counts))

    def facet_subtype(self, facets, qs):
        # count doctypes, subtypes in the current place first, so these are always shown as an option
        counts_in_place = {c["doctype"]: c["count"] for c in qs.filter(subtype=None).values("doctype").annotate(count=Count("doctype")).order_by()}
        counts_subtype_in_place = {c["subtype"]: c["count"] for c in qs.values("subtype").annotate(count=Count("subtype")).order_by()}
        counts_in_place.update(counts_subtype_in_place)

        qs = self.filter_queryset(qs, exclude="subtype")
        # count doctypes, subtypes by code
        counts = {c["doctype"]: c["count"] for c in qs.filter(subtype=None).values("doctype").annotate(count=Count("doctype")).order_by()}
        counts_subtype = {c["subtype"]: c["count"] for c in qs.values("subtype").annotate(count=Count("subtype")).order_by()}
        counts.update(counts_subtype)

        counts = [
            (st, n)
            for st, n in counts.items()
            if counts_in_place.get(st)
        ]
        facets.append(self.facet("subtype", "checkbox", counts))

    def facet_principal(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="principal")
        counts = qs.aggregate(
            principal_counts=Count("pk", filter=Q(principal=True), distinct=True),
            not_principal_counts=Count("pk", filter=Q(principal=False), distinct=True),
        )
        facets.append(self.facet("principal", "checkbox", [
            ("principal", counts.get("principal_counts", 0)),
            ("not_principal", counts.get("not_principal_counts", 0)),
        ]))

    def facet_stub(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="stub")
        counts = qs.aggregate(
            stub_counts=Count("pk", filter=Q(stub=True), distinct=True),
            not_stub_counts=Count("pk", filter=Q(stub=False), distinct=True),
        )
        facets.append(self.facet("stub", "checkbox", [
            ("stub", counts.get("stub_counts", 0)),
            ("not_stub", counts.get("not_stub_counts", 0)),
        ]))

    def facet_work_in_progress(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="work_in_progress")
        counts = qs.aggregate(
            work_in_progress_counts=Count("pk", filter=Q(work_in_progress=True), distinct=True),
            approved_counts=Count("pk", filter=Q(work_in_progress=False), distinct=True),
        )
        facets.append(self.facet("work_in_progress", "checkbox", [
            ("work_in_progress", counts.get("work_in_progress_counts", 0)),
            ("approved", counts.get("approved_counts", 0)),
        ]))

    def facet_tasks(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="tasks")
        task_states = qs.annotate(
            has_open_states=Count(
                Case(When(tasks__state__in=Task.OPEN_STATES, then=Value(1)), output_field=IntegerField())),
            has_unblocked_states=Count(
                Case(When(tasks__state__in=Task.UNBLOCKED_STATES, then=Value(1)), output_field=IntegerField())),
            has_blocked_states=Count(
                Case(When(tasks__state=Task.BLOCKED, then=Value(1)), output_field=IntegerField())),
        ).values('pk', 'has_open_states', 'has_unblocked_states', 'has_blocked_states')

        # Organize the results into totals per state
        counts = {'open_states': 0, 'unblocked_states': 0, 'only_blocked_states': 0, 'no_open_states': 0}

        for item in task_states:
            if item['has_open_states'] > 0:
                counts['open_states'] += 1
            else:
                counts['no_open_states'] += 1

            # unblocked and only blocked tasks
            if item['has_unblocked_states'] > 0:
                counts['unblocked_states'] += 1
            if item['has_blocked_states'] > 0 and not item['has_unblocked_states'] > 0:
                counts['only_blocked_states'] += 1

        facets.append(self.facet("tasks", "checkbox", [
            ("has_open_tasks", counts['open_states']),
            ("has_unblocked_tasks", counts['unblocked_states']),
            ("has_only_blocked_tasks", counts['only_blocked_states']),
            ("no_open_tasks", counts['no_open_states']),
        ]))

    def facet_primary(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="primary")
        counts = qs.aggregate(
            primary_counts=Count("pk", filter=Q(parent_work__isnull=True), distinct=True),
            subsidiary_counts=Count("pk", filter=Q(parent_work__isnull=False), distinct=True),
        )
        facets.append(self.facet("primary", "checkbox", [
            ("primary", counts.get("primary_counts", 0)),
            ("subsidiary", counts.get("subsidiary_counts", 0)),
        ]))

    def facet_commencement(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="commencement")
        counts = qs.aggregate(
            commenced_count=Count("pk", filter=Q(commenced=True), distinct=True),
            not_commenced_count=Count("pk", filter=Q(commenced=False), distinct=True),
            date_unknown_count=Count("pk", filter=Q(commencements__date__isnull=True, commenced=True), distinct=True),
        )
        qs = qs.annotate(Count("commencements"))
        counts['multipe_count'] = qs.filter(commencements__count__gt=1).count()
        facets.append(self.facet("commencement", "checkbox", [
            ("yes", counts.get("commenced_count", 0)),
            ("no", counts.get("not_commenced_count", 0)),
            ("date_unknown", counts.get("date_unknown_count", 0)),
            ("multiple", counts.get("multipe_count", 0)),
        ]))

    def facet_amendment(self, facet, qs):
        qs = self.filter_queryset(qs, exclude="amendment")
        counts = qs.aggregate(
            amended_count=Count("pk", filter=Q(amendments__isnull=False), distinct=True),
            not_amended_count=Count("pk", filter=Q(amendments__isnull=True), distinct=True),
        )
        facet.append(self.facet("amendment", "checkbox", [
            ("yes", counts.get("amended_count", 0)),
            ("no", counts.get("not_amended_count", 0)),
        ]))

    def facet_consolidation(self, facets,  qs):
        qs = self.filter_queryset(qs, exclude="consolidation")
        counts = qs.aggregate(
            has_consolidation=Count("pk", filter=Q(arbitrary_expression_dates__date__isnull=False), distinct=True),
            no_consolidation=Count("pk", filter=Q(arbitrary_expression_dates__date__isnull=True), distinct=True),
        )
        facets.append(self.facet("consolidation", "checkbox", [
            ("has_consolidation", counts.get("has_consolidation", 0)),
            ("no_consolidation", counts.get("no_consolidation", 0)),
        ]))

    def facet_publication_document(self, facets,  qs):
        qs = self.filter_queryset(qs, exclude="publication_document")
        counts = qs.aggregate(
            has_publication_document=Count("pk", filter=Q(publication_document__isnull=False), distinct=True),
            no_publication_document=Count("pk", filter=Q(publication_document__isnull=True), distinct=True),
        )
        facets.append(self.facet("publication_document", "checkbox", [
            ("has_publication_document", counts.get("has_publication_document", 0)),
            ("no_publication_document", counts.get("no_publication_document", 0)),
        ]))

    def facet_repeal(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="repeal")
        counts = qs.aggregate(
            repealed_count=Count("pk", filter=Q(repealed_date__isnull=False), distinct=True),
            not_repealed_count=Count("pk", filter=Q(repealed_date__isnull=True), distinct=True),
        )
        facets.append(self.facet("repeal", "checkbox", [
            ("yes", counts.get("repealed_count", 0)),
            ("no", counts.get("not_repealed_count", 0)),
        ]))

    def facet_points_in_time(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="documents")
        no_document_ids = qs.filter(document__isnull=True).values_list('pk', flat=True)
        deleted_document_ids = qs.filter(document__deleted=True).values_list('pk', flat=True)
        undeleted_document_ids = qs.filter(document__deleted=False).values_list('pk', flat=True)
        all_deleted_document_ids = deleted_document_ids.exclude(id__in=undeleted_document_ids)
        no_document_ids = list(no_document_ids) + list(all_deleted_document_ids)
        facets.append(self.facet("documents", "checkbox", [
            ("none", qs.annotate(Count('document')).filter(id__in=no_document_ids).count()),
            ("one", qs.filter(document__deleted=False).annotate(Count('document')).filter(document__count=1).count()),
            ("multiple", qs.filter(document__deleted=False).annotate(Count('document')).filter(document__count__gt=1).count()),
        ]))

    def facet_point_in_time_status(self, facets, qs):
        qs = self.filter_queryset(qs, exclude="status")
        counts = qs.aggregate(
            drafts_count=Count("pk", filter=Q(document__draft=True), distinct=True),
            published_count=Count("pk", filter=Q(document__draft=False), distinct=True),
        )
        facets.append(self.facet("status", "checkbox", [
            ("draft", counts.get("drafts_count", 0)),
            ("published", counts.get("published_count", 0)),
        ]))

    def facet_taxonomy(self, taxonomy_tree, qs):
        qs = self.filter_queryset(qs, exclude="taxonomy_topic")
        # count works per taxonomy topic
        counts = {
            x["taxonomy_topics__slug"]: x["count"]
            for x in qs.values("taxonomy_topics__slug").annotate(count=Count("pk", distinct=True)).order_by().values("taxonomy_topics__slug", "count")
        }

        # fold the counts into the taxonomy tree
        def decorate(item):
            total = 0
            for child in item.get('children', []):
                total = total + decorate(child)
            # count for this item
            item['data']['count'] = counts.get(item["data"]["slug"])
            # total of count for descendants
            item['data']['total'] = total
            return total + (item['data']['count'] or 0)

        for item in taxonomy_tree:
            decorate(item)

    def facet_place(self, place_tree, qs):
        if not place_tree:
            return

        qs = self.filter_queryset(qs, exclude="place")

        # count works per place
        counts = {}
        for row in qs.values("country__country__pk", "locality__code").annotate(count=Count("id")).order_by():
            code = row["country__country__pk"].lower()
            code = code + ("-" + row["locality__code"] if row["locality__code"] else "")
            counts[code] = row["count"]

        # fold the counts into the taxonomy tree
        def decorate(item):
            total = 0
            for child in item.get('children', []):
                total = total + decorate(child)
            # count for this item
            item['data']['count'] = counts.get(item["data"]["slug"])
            # total of count for descendants
            item['data']['total'] = total
            return total + (item['data']['count'] or 0)

        for item in place_tree:
            decorate(item)


class WorkChooserForm(forms.Form):
    country = forms.ModelChoiceField(queryset=Country.objects)
    locality = forms.ModelChoiceField(queryset=Locality.objects, required=False)
    q = forms.CharField(required=False)

    def clean_locality(self):
        # always update the queryset on the locality field for rendering (country may be None)
        self.fields['locality'].queryset = Locality.objects.filter(country=self.cleaned_data.get('country'))

        if self.cleaned_data.get('country'):
            if self.cleaned_data.get('locality') and self.cleaned_data['locality'].country != self.cleaned_data['country']:
                return None
        else:
            return None
        return self.cleaned_data['locality']

    def filter_queryset(self, qs):
        if self.cleaned_data.get('country'):
            qs = qs.filter(country=self.cleaned_data['country'])
            # only (and always) filter on locality if country is set -- locality=None for national works
            qs = qs.filter(locality=self.cleaned_data['locality'])

        if self.cleaned_data['q']:
            qs = qs.filter(Q(title__icontains=self.cleaned_data['q']) | Q(frbr_uri__icontains=self.cleaned_data['q']))

        return qs


class WorkBulkActionsForm(forms.Form):
    all_work_pks = forms.CharField(required=False)
    works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=True)

    def clean_all_work_pks(self):
        return self.cleaned_data.get('all_work_pks').split() or []

    def taxonomy_toc(self):
        # WorkBulkUpdateForm returns the real data when works are selected
        return []


class WorkBulkActionFormBase(forms.Form):
    """Base form for bulk work actions in the works listing view. Ensures that the works queryset is
    limited to the appropriate country, locality and user permissions.
    """
    works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=True)

    def __init__(self, country, locality, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if country.place_code == 'all':
            self.fields['works'].queryset = AllPlace.filter_works_queryset(self.fields['works'].queryset, user)
        else:
            self.fields['works'].queryset = self.fields['works'].queryset.filter(country=country, locality=locality)


class WorkBulkUpdateForm(WorkBulkActionFormBase):
    save = forms.BooleanField(required=False)
    works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=False)
    add_taxonomy_topics = forms.ModelMultipleChoiceField(
        queryset=TaxonomyTopic.objects.all(), to_field_name='slug',
        required=False)
    del_taxonomy_topics = forms.ModelMultipleChoiceField(
        queryset=TaxonomyTopic.objects.all(),
        required=False)

    def save_changes(self):
        if self.cleaned_data.get('add_taxonomy_topics'):
            for work in self.cleaned_data['works']:
                work.taxonomy_topics.add(*self.cleaned_data['add_taxonomy_topics'])

        if self.cleaned_data.get('del_taxonomy_topics'):
            for work in self.cleaned_data['works']:
                work.taxonomy_topics.remove(*self.cleaned_data['del_taxonomy_topics'])

    @cached_property
    def taxonomy_toc(self):
        return TaxonomyTopic.get_toc_tree()


class WorkBulkApproveForm(WorkBulkActionFormBase):
    TASK_CHOICES = [('', 'Create tasks'), ('block', _('Create and block tasks')), ('cancel', _('Create and cancel tasks'))]

    works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=False)
    conversion_task_description = forms.CharField(required=False)
    import_task_description = forms.CharField(required=False)
    gazette_task_description = forms.CharField(required=False)
    # amendment task descriptions are added per amendment on init
    update_conversion_tasks = forms.ChoiceField(choices=TASK_CHOICES, widget=RadioSelect, required=False)
    update_import_tasks = forms.ChoiceField(choices=TASK_CHOICES, widget=RadioSelect, required=False)
    update_gazette_tasks = forms.ChoiceField(choices=TASK_CHOICES, widget=RadioSelect, required=False)
    update_amendment_tasks = forms.ChoiceField(choices=TASK_CHOICES, widget=RadioSelect, required=False)
    # TODO: add multichoice label dropdown per task type too
    approve = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        broker_class = kwargs.pop('broker_class', TaskBroker)
        super().__init__(*args, **kwargs)
        if self.is_valid():
            self.broker = broker_class(self.cleaned_data.get('works', []))
            self.add_amendment_task_description_fields()
            self.full_clean()

    def add_amendment_task_description_fields(self):
        for amendment in self.broker.amendments:
            self.fields[f'amendment_task_create_{amendment.pk}'] = forms.BooleanField(initial=True, required=False)
            self.fields[f'amendment_task_description_{amendment.pk}'] = forms.CharField()

    def save_changes(self, request):
        for work in self.broker.works:
            work.approve(request.user, request)

        self.broker.create_tasks(request.user, self.cleaned_data)


class WorkBulkUnapproveForm(WorkBulkActionFormBase):
    works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=False)
    unapprove = forms.BooleanField(required=False)


class WorkBulkLinkRefsForm(WorkBulkActionFormBase):
    link_refs = forms.BooleanField(required=False)
    unlink = forms.BooleanField(required=False)


class BatchCreateWorkForm(forms.Form):
    spreadsheet_url = forms.URLField(required=True, validators=[
        URLValidator(
            schemes=['https'],
            regex='^https:\/\/docs.google.com\/spreadsheets\/d\/\S+\/',
            message=_("Please enter a valid Google Sheets URL, such as https://docs.google.com/spreadsheets/d/ABCXXX/"), code='bad')
    ])
    sheet_name = forms.ChoiceField(required=False, choices=[])
    taxonomy_topic = forms.ModelChoiceField(queryset=TaxonomyTopic.objects.filter(slug__startswith='projects-', depth__gte=3), empty_label='Choose a topic')
    block_conversion_tasks = forms.BooleanField(initial=False, required=False)
    cancel_conversion_tasks = forms.BooleanField(initial=False, required=False)
    block_import_tasks = forms.BooleanField(initial=False, required=False)
    cancel_import_tasks = forms.BooleanField(initial=False, required=False)
    block_gazette_tasks = forms.BooleanField(initial=False, required=False)
    cancel_gazette_tasks = forms.BooleanField(initial=False, required=False)
    block_amendment_tasks = forms.BooleanField(initial=False, required=False)
    cancel_amendment_tasks = forms.BooleanField(initial=False, required=False)
    tasks = forms.MultipleChoiceField(
        choices=(('import-content', _('Import content')), ('link-gazette', _('Link gazette'))), required=False)


class ColumnSelectWidget(SelectMultiple):
    # TODO: get these core fields from somewhere else? cobalt / FRBR URI fields?
    core_fields = ['actor', 'country', 'locality', 'doctype', 'subtype', 'number', 'year']
    unavailable_fields = [
        'commenced_by', 'commenced_on_date', 'commences', 'commences_on_date',
        'amended_by', 'amended_on_date', 'amends', 'amends_on_date',
        'repealed_by', 'repealed_on_date', 'repeals', 'repeals_on_date',
        'primary_work', 'subleg', 'taxonomy', 'taxonomy_topic'
    ]

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)

        option['attrs']['disabled'] = option['value'] in self.core_fields + self.unavailable_fields
        if option['value'] in self.core_fields:
            option['label'] = f'Core field: {option["label"]}'
        if option['value'] in self.unavailable_fields:
            option['label'] = f'Unavailable: {option["label"]}'

        return option


class BatchUpdateWorkForm(BatchCreateWorkForm):
    update_columns = forms.MultipleChoiceField()
    taxonomy_topic = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from indigo.bulk_creator import RowValidationFormBase
        row_validation_form = RowValidationFormBase
        fields = list(row_validation_form.base_fields)
        fields.remove('row_number')
        self.fields['update_columns'].widget = ColumnSelectWidget()
        # TODO: include place's extra properties
        self.fields['update_columns'].choices = ([(x, re.sub('_', ' ', x).capitalize()) for x in fields])
        self.fields['update_columns'].choices.sort(key=lambda x: x[1])
