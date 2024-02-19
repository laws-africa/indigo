import re
from datetime import date
from functools import cached_property

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import Q, Count
from django.forms import SelectMultiple, RadioSelect, formset_factory
from django.utils.translation import gettext as _, gettext_lazy as _l

from cobalt import FrbrUri
from indigo_api.models import Work, VocabularyTopic, TaxonomyTopic, Amendment, Subtype, Locality, PublicationDocument, \
    Commencement, Workflow, Task, Country
from indigo_app.forms.mixins import FormAsUrlMixin


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = (
            'title', 'frbr_uri', 'assent_date', 'parent_work', 'commenced', 'commencement_date', 'commencing_work',
            'repealed_by', 'repealed_date', 'publication_name', 'publication_number', 'publication_date',
            'publication_document_trusted_url', 'publication_document_size', 'publication_document_mime_type',
            'stub', 'principal', 'taxonomies', 'taxonomy_topics', 'as_at_date_override', 'consolidation_note_override', 'country', 'locality',
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
    taxonomies = forms.ModelMultipleChoiceField(
        queryset=VocabularyTopic.objects
            .select_related('vocabulary')
            .order_by('vocabulary__title', 'level_1', 'level_2'),
        required=False)
    taxonomy_topics = forms.ModelMultipleChoiceField(
        queryset=TaxonomyTopic.objects.all(),
        required=False)
    publication_document_trusted_url = forms.URLField(required=False)
    publication_document_size = forms.IntegerField(required=False)
    publication_document_mime_type = forms.CharField(required=False)

    # custom work properties that shouldn't be rendered automatically.
    # this assumes that these properties are rendered manually on the form
    # page.
    no_render_properties = []

    # commencement details
    commencement_date = forms.DateField(required=False)
    commencing_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    commencement_note = forms.CharField(max_length=1024, required=False)

    def __init__(self, country, locality, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country = country
        self.locality = locality
        self.place = locality or country
        self.user = user

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
            self.fields['commencement_date'].initial = self.instance.commencement_date
            self.fields['commencement_note'].initial = self.instance.commencement_note
            if hasattr(self.instance.main_commencement, 'commencing_work'):
                if self.instance.main_commencement.commencing_work:
                    self.fields['commencing_work'].initial = self.instance.main_commencement.commencing_work.pk

            # repeal formset
            self.RepealMadeBaseFormSet = RepealMadeBaseFormSet
            repeals_made_formset_kwargs = {
                "form_kwargs": {
                    "work": self.instance,
                },
                "prefix": "repeals_made",
                "initial": [{
                    "repealed_work": repealed_work,
                    "repealed_date": repealed_work.repealed_date,
                } for repealed_work in self.instance.repealed_works.all()]
            }
            if self.is_bound:
                repeals_made_formset_kwargs["data"] = self.data

            self.repeals_made_formset = self.RepealMadeBaseFormSet(**repeals_made_formset_kwargs)

            self.AmendmentsBaseFormSet = AmendmentsBaseFormSet

            amended_by_formset_kwargs = {
                "form_kwargs": {
                    "work": self.instance,
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

            self.amended_by_formset = self.AmendmentsBaseFormSet(**amended_by_formset_kwargs)

            amendments_made_formset_kwargs = {
                "form_kwargs": {
                    "work": self.instance,
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

            self.amendments_made_formset = self.AmendmentsBaseFormSet(**amendments_made_formset_kwargs)

            self.CommencementsMadeBaseFormset = CommencementsMadeBaseFormset

            commencements_made_formset_kwargs = {
                "form_kwargs": {
                    "work": self.instance,
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

            self.commencements_made_formset = self.CommencementsMadeBaseFormset(**commencements_made_formset_kwargs)

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
        if self.instance.pk:
            return (
                    super().is_valid() and
                    self.repeals_made_formset.is_valid() and
                    self.amended_by_formset.is_valid() and
                    self.amendments_made_formset.is_valid() and
                    self.commencements_made_formset.is_valid()
            )
        return super().is_valid()

    def has_changed(self):
        if self.instance.pk:
            return (
                    super().has_changed() or
                    self.repeals_made_formset.has_changed() or
                    self.amended_by_formset.has_changed() or
                    self.amendments_made_formset.has_changed() or
                    self.commencements_made_formset.has_changed()
            )
        return super().has_changed()

    def clean_frbr_number(self):
        value = self.cleaned_data['frbr_number']
        value = re.sub(r'[\s!?@#$§±%^&*;:,.<>(){}\[\]\\/|"\'“”‘’‟„‛‚«»‹›]+', '-', value, flags=re.IGNORECASE)
        value = re.sub(r'--+', '-', value)
        return value

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
        self.save_commencement()
        self.save_repeals()
        self.save_amended_by()
        self.save_amendments_made()
        self.save_commencements_made()
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

    def save_repeals(self):
        for repeal_form in self.repeals_made_formset:
            if repeal_form.is_valid() and repeal_form.has_changed():
                repeal_form.save(self.user)

    def save_amended_by(self):
        for form in self.amended_by_formset:
            if form.is_valid() and form.has_changed():
                form.save(self.user)

    def save_amendments_made(self):
        for form in self.amendments_made_formset:
            if form.is_valid() and form.has_changed():
                form.save(self.user)

    def save_commencements_made(self):
        self.commencements_made_formset.save(self.user, self.instance)

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

    def save_commencement(self):
        work = self.instance

        # if there are multiple commencement objects, then just ignore these elements,
        # the user must edit the commencements in the commencements view
        if work.commencements.count() > 1:
            return

        # if the work has either been created as uncommenced or edited not to commence, delete all existing commencements
        if not work.commenced:
            for obj in work.commencements.all():
                obj.delete()

        else:
            # if the work has either been created as commenced or edited to commence, update / create the commencement
            commencement, created = Commencement.objects.get_or_create(
                defaults={'created_by_user': work.updated_by_user},
                commenced_work=work
            )
            commencement.updated_by_user = work.updated_by_user
            commencement.commencing_work = self.cleaned_data['commencing_work']
            commencement.note = self.cleaned_data['commencement_note']
            commencement.date = self.cleaned_data['commencement_date']
            if created:
                commencement.all_provisions = True
            # this is safe because we know there are no other commencement objects
            commencement.main = True
            commencement.save()


class AmendmentForm(forms.ModelForm):
    amending_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    amended_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Amendment
        fields = ('amending_work', 'amended_work', 'date', 'id')

    def __init__(self, work, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.work = work

    @cached_property
    def amending_work_obj(self):
        return Work.objects.filter(pk=self['amending_work'].value()).first()

    @cached_property
    def amended_work_obj(self):
        return Work.objects.filter(pk=self['amended_work'].value()).first()

    def save(self, user, *args, **kwargs):
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
                amendment.updated_by_user = user
                amendment.save()
            else:
                Amendment.objects.create(
                    amended_work=self.cleaned_data['amended_work'],
                    amending_work=self.cleaned_data['amending_work'],
                    date=self.cleaned_data["date"],
                    created_by_user=user,
                    updated_by_user=user,
                )


AmendmentsFormSet = formset_factory(
    AmendmentForm,
    extra=0,
    can_delete=True,
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
                raise ValidationError("Amending work and date must be unique together.")
            seen.add((amending_work, amended_work, date))


class RepealMadeForm(forms.Form):
    repealed_work = forms.ModelChoiceField(queryset=Work.objects)
    repealed_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, work, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.work = work

    @cached_property
    def repealed_work_obj(self):
        return Work.objects.filter(pk=self['repealed_work'].value()).first()

    def is_repealed_work_saved(self):
        return self.repealed_work_obj.repealed_by == self.work

    def save(self, user):
        work = self.cleaned_data['repealed_work']
        if self.cleaned_data.get('DELETE'):
            if work.repealed_by == self.work:
                work.repealed_by = None
                work.repealed_date = None
                work.save_with_revision(user=user)
        else:
            work.repealed_by = self.work
            work.repealed_date = self.cleaned_data['repealed_date']
            work.save_with_revision(user=user)


RepealMadeFormSet = formset_factory(
    RepealMadeForm,
    extra=0,
    can_delete=True,
)


class RepealMadeBaseFormSet(RepealMadeFormSet):
    pass


class FindPubDocForm(forms.Form):
    name = forms.CharField(required=False, widget=forms.HiddenInput())
    trusted_url = forms.URLField(required=False, widget=forms.HiddenInput())
    size = forms.IntegerField(required=False, widget=forms.HiddenInput())
    mimetype = forms.CharField(required=False, widget=forms.HiddenInput())


class NewCommencementForm(forms.ModelForm):
    commencing_work = forms.ModelChoiceField(Work.objects, required=False)

    class Meta:
        model = Commencement
        fields = ('date', 'commencing_work')

    def clean(self):
        super().clean()
        if not self.cleaned_data['date'] and not self.cleaned_data['commencing_work']:
            # create one for now
            self.cleaned_data['date'] = date.today()


class CommencementForm(forms.ModelForm):
    provisions = forms.MultipleChoiceField(required=False)

    class Meta:
        model = Commencement
        fields = ('date', 'all_provisions', 'provisions', 'main', 'note')

    def __init__(self, work, provisions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.work = work
        self.provisions = provisions
        self.fields['provisions'].choices = [(p.id, p.title) for p in self.provisions]

    def clean_main(self):
        if self.cleaned_data['main']:
            # there can be only one!
            qs = Commencement.objects.filter(commenced_work=self.work, main=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A main commencement already exists.")
        return self.cleaned_data['main']

    def clean_all_provisions(self):
        if self.cleaned_data['all_provisions']:
            # there can be only one!
            qs = Commencement.objects.filter(commenced_work=self.work)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A commencement for all provisions must be the only commencement.")
        return self.cleaned_data['all_provisions']

    def clean(self):
        super().clean()
        if self.cleaned_data['all_provisions'] and self.cleaned_data['provisions']:
            raise ValidationError("Cannot specify all provisions, and a list of provisions.")

class CommencementsPartialForm(forms.Form):
    commencing_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    commenced_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
    note = forms.CharField(required=False, widget=forms.TextInput)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    # class Meta:
    #     model = Commencement
    #     fields = ('commencing_work', 'commenced_work', 'date', 'id', 'note',)

    def __init__(self, work, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.work = work

    @cached_property
    def commencing_work_obj(self):
        return Work.objects.filter(pk=self['commencing_work'].value()).first()

    @cached_property
    def commenced_work_obj(self):
        return Work.objects.filter(pk=self['commenced_work'].value()).first()

    def save(self, user, *args, **kwargs):
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
                commencement.updated_by_user = user
                commencement.save()
            else:
                Commencement.objects.create(
                    commencing_work=self.cleaned_data['commencing_work'],
                    commenced_work=self.cleaned_data['commenced_work'],
                    date=self.cleaned_data["date"],
                    note=self.cleaned_data["note"],
                    created_by_user=user,
                    updated_by_user=user,
                )

CommencementsFormset = formset_factory(
    CommencementsPartialForm,
    extra=0,
    can_delete=True,
)

class CommencementsMadeBaseFormset(CommencementsFormset):


    def clean(self):
        super().clean()
        if any(self.errors):
            return
        # check if commencing work and date are unique together
        seen = set()
        for form in self.forms:
            if form.cleaned_data.get('DELETE'):
                continue
            amending_work = form.cleaned_data.get('commencing_work')
            amended_work = form.cleaned_data.get('commenced_work')
            date = form.cleaned_data.get('date')
            if (amending_work, amended_work, date) in seen:
                raise ValidationError("Commenced work and date must be unique together.")
            seen.add((amending_work, amended_work, date))

    def save(self, user, work, *args, **kwargs):
        if self.is_valid() and self.has_changed():
            for form in self.forms:
                form.save(user)

            commenced_counts = Commencement.objects.filter(commencing_work=work).values("commenced_work").annotate(num_commencements=Count("id")).order_by()
            multiple_commencements = commenced_counts.filter(num_commencements__gt=1).values_list("commenced_work", flat=True)
            single_commencements = commenced_counts.filter(num_commencements=1).values_list("commenced_work", flat=True)

            for commencement in multiple_commencements:
                commencements = Commencement.objects.filter(commencing_work=work,
                                                            commenced_work=commencement).order_by("date")
                # update all commencements first
                for c in commencements:
                    c.main = False
                    c.all_provisions = False
                    c.save()

                # update the first commencement to be the main one
                first = commencements.first()
                first.main = True
                first.save()

            for commencement in single_commencements:
                c = Commencement.objects.filter(commencing_work=work, commenced_work=commencement).first()
                c.main = True
                c.all_provisions = True
                c.save()


class WorkFilterForm(forms.Form, FormAsUrlMixin):
    q = forms.CharField()

    assent_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    assent_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    publication_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    publication_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    amendment = forms.MultipleChoiceField(choices=[('', 'Any'), ('no', 'Not amended'), ('yes', 'Amended')])
    amendment_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    amendment_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    commencement = forms.MultipleChoiceField(choices=[('', 'Any'), ('no', 'Not commenced'), ('date_unknown', 'Commencement date unknown'), ('yes', 'Commenced'), ('partial', 'Partially commenced'), ('multiple', 'Multiple commencements')])
    commencement_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    commencement_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    repeal = forms.MultipleChoiceField(choices=[('', 'Any'), ('no', 'Not repealed'), ('yes', 'Repealed')])
    repealed_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    repealed_date_end = forms.DateField(input_formats=['%Y-%m-%d'])

    stub = forms.MultipleChoiceField(choices=[('stub', 'Stub'), ('not_stub', 'Not a stub'), ])
    work_in_progress = forms.MultipleChoiceField(choices=[('work_in_progress', 'Work in progress'), ('approved', 'Approved')])
    status = forms.MultipleChoiceField(choices=[('published', 'published'), ('draft', 'draft')])
    sortby = forms.ChoiceField(choices=[
        ('-created_at', _l('Created at (newest first)')), ('created_at', _l('Created at (oldest first)')),
        ('-updated_at', _l('Updated at (newest first)')), ('updated_at', _l('Updated at (oldest first)')),
        ('title', _l('Title (A-Z)')), ('-title', _l('Title (Z-A)')),
        ('date', _l('Date (oldest first)')), ('-date', _l('Date (newest first)')),
        ('number', _l('Number (ascending)')), ('-number', _l('Number (descending)')),
    ])
    principal = forms.MultipleChoiceField(required=False, choices=[('principal', 'Principal'), ('not_principal', 'Not Principal')])
    tasks = forms.MultipleChoiceField(required=False, choices=[('has_open_tasks', 'Has open tasks'), ('has_unblocked_tasks', 'Has unblocked tasks'), ('has_only_blocked_tasks', 'Has only blocked tasks'), ('no_open_tasks', 'Has no open tasks')])
    primary = forms.MultipleChoiceField(required=False, choices=[('primary', 'Primary'), ('primary_subsidiary', 'Primary with subsidiary'), ('subsidiary', 'Subsidiary')])
    consolidation = forms.MultipleChoiceField(required=False, choices=[('has_consolidation', 'Has consolidation'), ('no_consolidation', 'No consolidation')])
    publication_document = forms.MultipleChoiceField(required=False, choices=[('has_publication_document', 'Has publication document'), ('no_publication_document', 'No publication document')])
    documents = forms.MultipleChoiceField(required=False, choices=[('one', 'Has one document'), ('multiple', 'Has multiple documents'), ('none', 'Has no documents'), ('published', 'Has published document(s)'), ('draft', 'Has draft document(s)')])
    taxonomy_topic = forms.ModelMultipleChoiceField(queryset=TaxonomyTopic.objects, to_field_name='slug', required=False)

    advanced_filters = ['assent_date_start', 'publication_date_start', 'repealed_date_start', 'amendment_date_start', 'commencement_date_start']

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super().__init__(*args, **kwargs)
        doctypes = [(d[1].lower(), d[0]) for d in
                    settings.INDIGO['DOCTYPES'] +
                    settings.INDIGO['EXTRA_DOCTYPES'].get(self.country.code, [])]
        subtypes = [(s.abbreviation, s.name) for s in Subtype.objects.all()]
        self.fields['subtype'] = forms.MultipleChoiceField(required=False, choices=doctypes + subtypes)

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

        # filter by work in progress
        if exclude != "work_in_progress":
            work_in_progress_filter = self.cleaned_data.get('work_in_progress', [])
            work_in_progress_qs = Q()
            if "work_in_progress" in work_in_progress_filter:
                work_in_progress_qs |= Q(work_in_progress=True)
            if "approved" in work_in_progress_filter:
                work_in_progress_qs |= Q(work_in_progress=False)

            queryset = queryset.filter(work_in_progress_qs)

        # filter by stub
        if exclude != "stub":
            stub_filter = self.cleaned_data.get('stub', [])
            stub_qs = Q()
            if "stub" in stub_filter:
                stub_qs |= Q(stub=True)
            if "not_stub" in stub_filter:
                stub_qs |= Q(stub=False)

            queryset = queryset.filter(stub_qs)

        # filter by principal
        if exclude != "principal":
            principal_filter = self.cleaned_data.get('principal', [])
            principal_qs = Q()
            if "principal" in principal_filter:
                principal_qs |= Q(principal=True)
            if "not_principal" in principal_filter:
                principal_qs |= Q(principal=False)

            queryset = queryset.filter(principal_qs)

        # filter by tasks status
        if exclude != "tasks":
            tasks_filter = self.cleaned_data.get('tasks', [])
            tasks_qs = Q()
            if "has_open_tasks" in tasks_filter:
                open_task_ids = queryset.filter(tasks__state__in=Task.OPEN_STATES).values_list('pk', flat=True)
                tasks_qs |= Q(id__in=open_task_ids)
            if "has_unblocked_tasks" in tasks_filter:
                unblocked_task_ids = queryset.filter(tasks__state__in=Task.UNBLOCKED_STATES).values_list('pk', flat=True)
                tasks_qs |= Q(id__in=unblocked_task_ids)
            if "has_only_blocked_tasks" in tasks_filter:
                only_blocked_task_ids = queryset.filter(tasks__state=Task.BLOCKED).exclude(tasks__state__in=Task.UNBLOCKED_STATES).values_list('pk', flat=True)
                tasks_qs |= Q(id__in=only_blocked_task_ids)
            if "no_open_tasks" in tasks_filter:
                no_open_task_ids = queryset.exclude(tasks__state__in=Task.OPEN_STATES).values_list('pk', flat=True)
                tasks_qs |= Q(id__in=no_open_task_ids)

            queryset = queryset.filter(tasks_qs)

        # filter by primary or subsidiary work
        if exclude != "primary":
            primary_filter = self.cleaned_data.get('primary', [])
            primary_qs = Q()
            if "primary" in primary_filter:
                primary_qs |= Q(parent_work__isnull=True)
            if "subsidiary" in primary_filter:
                primary_qs |= Q(parent_work__isnull=False)

            queryset = queryset.filter(primary_qs)

        # doctype, subtype
        if exclude != "subtype":
            subtype_filter = self.cleaned_data.get("subtype", [])
            subtype_qs = Q()
            subtypes = [s.abbreviation for s in Subtype.objects.all()]
            for subtype in subtype_filter:
                if subtype in subtypes:
                    subtype_qs |= Q(subtype=subtype)
                else:
                    subtype_qs |= Q(doctype=subtype, subtype=None)

            queryset = queryset.filter(subtype_qs)

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
            repeal_filter = self.cleaned_data.get('repeal', [])
            repeal_qs = Q()
            if "yes" in repeal_filter:
                repeal_qs |= Q(repealed_date__isnull=False)
            if "no" in repeal_filter:
                repeal_qs |= Q(repealed_date__isnull=True)

            queryset = queryset.filter(repeal_qs)

        if self.cleaned_data.get('repealed_date_start') and self.cleaned_data.get('repealed_date_end'):
            start_date = self.cleaned_data['repealed_date_start']
            end_date = self.cleaned_data['repealed_date_end']
            queryset = queryset.filter(repealed_date__range=[start_date, end_date]).order_by('-repealed_date')

        # filter by amendment
        if exclude != "amendment":
            amendment_filter = self.cleaned_data.get('amendment', [])
            amendment_qs = Q()
            if "yes" in amendment_filter:
                amendment_qs |= Q(amendments__date__isnull=False)
            if 'no' in amendment_filter:
                amendment_qs |= Q(amendments__date__isnull=True)

            queryset = queryset.filter(amendment_qs)

        if self.cleaned_data.get('amendment_date_start') and self.cleaned_data.get('amendment_date_end'):
            start_date = self.cleaned_data['amendment_date_start']
            end_date = self.cleaned_data['amendment_date_end']
            queryset = queryset.filter(amendments__date__range=[start_date, end_date]).order_by('-amendments__date')

        # filter by commencement status
        if exclude != "commencement":
            commencement_filter = self.cleaned_data.get('commencement', [])
            commencement_qs = Q()
            if 'yes' in commencement_filter:
                commencement_qs |= Q(commenced=True)
            if 'no' in commencement_filter:
                commencement_qs |= Q(commenced=False)
            if 'date_unknown' in commencement_filter:
                commencement_qs |= Q(commencements__date__isnull=True, commenced=True)
            if 'multiple' in commencement_filter:
                queryset = queryset.annotate(Count("commencements"))
                commencement_qs |= Q(commencements__count__gt=1)

            queryset = queryset.filter(commencement_qs)

        if self.cleaned_data.get('commencement_date_start') and self.cleaned_data.get('commencement_date_end'):
            start_date = self.cleaned_data['commencement_date_start']
            end_date = self.cleaned_data['commencement_date_end']
            queryset = queryset.filter(commencements__date__range=[start_date, end_date]).order_by('-commencements__date')

        # filter by consolidation
        if exclude != "consolidation":
            consolidation_filter = self.cleaned_data.get('consolidation', [])
            consolidation_qs = Q()
            if 'has_consolidation' in consolidation_filter:
                consolidation_qs |= Q(arbitrary_expression_dates__date__isnull=False)
            if 'no_consolidation' in consolidation_filter:
                consolidation_qs |= Q(arbitrary_expression_dates__date__isnull=True)

            queryset = queryset.filter(consolidation_qs)

        # filter by publication document
        if exclude != "publication_document":
            publication_document_filter = self.cleaned_data.get('publication_document', [])
            publication_document_qs = Q()
            if 'has_publication_document' in publication_document_filter:
                publication_document_qs |= Q(publication_document__isnull=False)
            if 'no_publication_document' in publication_document_filter:
                publication_document_qs |= Q(publication_document__isnull=True)

            queryset = queryset.filter(publication_document_qs)

        # filter by points in time
        if exclude != "documents":
            documents_filter = self.cleaned_data.get('documents', [])
            documents_qs = Q()
            if 'one' in documents_filter:
                one_document_ids = queryset.filter(document__deleted=False).annotate(Count('document')).filter(document__count=1).values_list('pk', flat=True)
                documents_qs |= Q(id__in=one_document_ids)
            if 'multiple' in documents_filter:
                multiple_document_ids = queryset.filter(document__deleted=False).annotate(Count('document')).filter(document__count__gt=1).values_list('pk', flat=True)
                documents_qs |= Q(id__in=multiple_document_ids)
            if 'none' in documents_filter:
                # either there are no documents at all
                documents_qs |= Q(document__isnull=True)
                # or they're all deleted
                deleted_document_ids = queryset.filter(document__deleted=True).values_list('pk', flat=True)
                undeleted_document_ids = queryset.filter(document__deleted=False).values_list('pk', flat=True)
                all_deleted_document_ids = deleted_document_ids.exclude(id__in=undeleted_document_ids)
                documents_qs |= Q(id__in=all_deleted_document_ids)

            queryset = queryset.filter(documents_qs)

        # filter by point in time status
        if exclude != "status":
            status_filter = self.cleaned_data.get('status', [])
            status_qs = Q()
            if 'draft' in status_filter:
                status_qs |= Q(document__draft=True)
            if 'published' in status_filter:
                status_qs |= Q(document__draft=False)

            queryset = queryset.filter(status_qs)

        # filter by taxonomy topic
        if exclude != "taxonomy_topic":
            if self.cleaned_data.get('taxonomy_topic'):
                queryset = queryset.filter(taxonomy_topics__in=self.cleaned_data['taxonomy_topic'])

        # sort by
        if self.cleaned_data.get('sortby'):
            queryset = queryset.order_by(self.cleaned_data.get('sortby'))

        return queryset.distinct()


class WorkChooserForm(forms.Form):
    country = forms.ModelChoiceField(queryset=Country.objects)
    locality = forms.ModelChoiceField(queryset=Locality.objects, required=False)
    q = forms.CharField(required=False)

    def clean_locality(self):
        if self.cleaned_data.get('country'):
            # update the queryset on the locality field for rendering
            self.fields['locality'].queryset = Locality.objects.filter(country=self.cleaned_data['country'])
            if self.cleaned_data.get('locality') and self.cleaned_data['locality'].country != self.cleaned_data['country']:
                return None
        else:
            return None
        return self.cleaned_data['locality']

    def filter_queryset(self, qs):
        if self.cleaned_data['country']:
            qs = qs.filter(country=self.cleaned_data['country'])

        if self.cleaned_data['locality']:
            qs = qs.filter(locality=self.cleaned_data['locality'])

        if self.cleaned_data['q']:
            qs = qs.filter(title__icontains=self.cleaned_data['q'])

        return qs


class WorkBulkActionsForm(forms.Form):
    all_work_pks = forms.CharField(required=False)
    works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=True)

    def clean_all_work_pks(self):
        return self.cleaned_data.get('all_work_pks').split() or []


class WorkBulkUpdateForm(forms.Form):
    save = forms.BooleanField(required=False)
    works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=False)
    add_taxonomy_topics = forms.ModelMultipleChoiceField(
        queryset=TaxonomyTopic.objects.all(),
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


class WorkBulkApproveForm(forms.Form):
    TASK_CHOICES = [('', 'Create tasks'), ('block', 'Create and block tasks'), ('cancel', 'Create and cancel tasks')]
    works_in_progress = forms.ModelMultipleChoiceField(queryset=Work.objects, required=False)
    import_task_works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=False)
    update_import_tasks = forms.ChoiceField(choices=TASK_CHOICES, widget=RadioSelect, required=False)
    import_task_description = forms.CharField(required=False)
    gazette_task_works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=False)
    update_gazette_tasks = forms.ChoiceField(choices=TASK_CHOICES, widget=RadioSelect, required=False)
    gazette_task_description = forms.CharField(required=False)
    amendment_task_works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=False)
    update_amendment_tasks = forms.ChoiceField(choices=TASK_CHOICES, widget=RadioSelect, required=False)
    # TODO: add multichoice label dropdown per task type too
    approve = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_valid():
            self.add_amendment_task_description_fields(self.cleaned_data.get('works_in_progress', []))
            self.full_clean()

    def add_amendment_task_description_fields(self, works_in_progress):
        for work in works_in_progress:
            for amendment in work.amendments.all():
                self.fields[f'amendment_task_description_{amendment.pk}'] = forms.CharField()

    def save_changes(self, request):
        for work in self.cleaned_data["works_in_progress"]:
            work.approve(request.user, request)

        # import tasks
        if self.cleaned_data.get('import_task_works'):
            # TODO: add the appropriate timeline date for Import tasks too?
            import_tasks = [self.get_or_create_task(work=work, task_type='import-content', description=self.cleaned_data['import_task_description'], user=request.user) for work in self.cleaned_data['import_task_works']]
            if self.cleaned_data.get('update_import_tasks'):
                self.block_or_cancel_tasks(import_tasks, self.cleaned_data['update_import_tasks'], request.user)

        # gazette tasks
        if self.cleaned_data.get('gazette_task_works'):
            gazette_tasks = [self.get_or_create_task(work=work, task_type='link-gazette', description=self.cleaned_data['gazette_task_description'], user=request.user) for work in self.cleaned_data['gazette_task_works']]
            if self.cleaned_data.get('update_gazette_tasks'):
                self.block_or_cancel_tasks(gazette_tasks, self.cleaned_data['update_gazette_tasks'], request.user)

        # amendment tasks
        if self.cleaned_data.get('amendment_task_works'):
            amendment_tasks = []
            for work in self.cleaned_data['amendment_task_works']:
                for amendment in work.amendments.all():
                    amendment_tasks.append(self.get_or_create_task(
                        work=work, task_type='apply-amendment',
                        description=self.cleaned_data[f'amendment_task_description_{amendment.pk}'],
                        user=request.user, timeline_date=amendment.date))
            if self.cleaned_data.get('update_amendment_tasks'):
                self.block_or_cancel_tasks(amendment_tasks, self.cleaned_data['update_amendment_tasks'], request.user)

    def get_or_create_task(self, work, task_type, description, user, timeline_date=None):
        task_titles = {
            'import-content': _('Import content'),
            'link-gazette': _('Link Gazette'),
            'apply-amendment': _('Apply amendment'),
        }
        task_title = task_titles[task_type]

        task = Task.objects.filter(work=work, code=task_type, timeline_date=timeline_date).first()
        if not task:
            task = Task(country=work.country, locality=work.locality, work=work,
                        code=task_type, timeline_date=timeline_date, created_by_user=user)

        task.title = task_title
        task.description = description
        task.updated_by_user = user
        task.save()

        # reopen or unblock tasks: they'll be blocked or cancelled again if needed as chosen in the form
        # TODO: only leave closed tasks as done if they should be:
        #  Gazette tasks never (we've already checked),
        #  Import / Amendment tasks only if there's a published document at the timeline date
        if task.state == Task.CANCELLED:
            task.reopen(user)
        elif task.state == Task.BLOCKED and not task.blocked_by.exists():
            task.unblock(user)

        return task

    def block_or_cancel_tasks(self, tasks, block_or_cancel, user):
        for task in tasks:
            if block_or_cancel == 'block':
                task.block(user)
            elif block_or_cancel == 'cancel':
                task.cancel(user)


class WorkBulkUnapproveForm(forms.Form):
    approved_works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=False)
    unapprove = forms.BooleanField(required=False)


class BatchCreateWorkForm(forms.Form):
    spreadsheet_url = forms.URLField(required=True, validators=[
        URLValidator(
            schemes=['https'],
            regex='^https:\/\/docs.google.com\/spreadsheets\/d\/\S+\/',
            message="Please enter a valid Google Sheets URL, such as https://docs.google.com/spreadsheets/d/ABCXXX/", code='bad')
    ])
    sheet_name = forms.ChoiceField(required=False, choices=[])
    workflow = forms.ModelChoiceField(queryset=Workflow.objects, empty_label="(None)", required=False)
    taxonomy_topic = forms.ModelChoiceField(queryset=TaxonomyTopic.objects.filter(slug__startswith='projects-', depth__gte=3), empty_label='Choose a topic')
    block_import_tasks = forms.BooleanField(initial=False, required=False)
    cancel_import_tasks = forms.BooleanField(initial=False, required=False)
    block_gazette_tasks = forms.BooleanField(initial=False, required=False)
    cancel_gazette_tasks = forms.BooleanField(initial=False, required=False)
    block_amendment_tasks = forms.BooleanField(initial=False, required=False)
    cancel_amendment_tasks = forms.BooleanField(initial=False, required=False)
    tasks = forms.MultipleChoiceField(
        choices=(('import-content', 'Import content'), ('link-gazette', 'Link gazette')), required=False)


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
