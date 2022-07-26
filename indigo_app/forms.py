import json
import re
import urllib.parse
from datetime import date
from lxml import etree

from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from django.core.validators import URLValidator
from django.conf import settings
from captcha.fields import ReCaptchaField
from allauth.account.forms import SignupForm

from indigo_app.models import Editor
from indigo_api.models import Document, Country, Language, Work, PublicationDocument, Task, TaskLabel, User, Subtype, \
    Workflow, \
    VocabularyTopic, Commencement, PlaceSettings


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = (
            'title', 'frbr_uri', 'assent_date', 'parent_work', 'commenced', 'commencement_date', 'commencing_work',
            'repealed_by', 'repealed_date', 'publication_name', 'publication_number', 'publication_date',
            'publication_document_trusted_url', 'publication_document_size', 'publication_document_mime_type',
            'stub', 'taxonomies', 'as_at_date_override', 'consolidation_note_override', 'country', 'locality',
        )

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

    def __init__(self, place, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.place = place

        for prop, label in self.place.settings.work_properties.items():
            key = f'property_{prop}'
            if self.instance:
                self.initial[key] = self.instance.properties.get(prop)
            self.fields[key] = forms.CharField(label=label, required=False)

    def property_fields(self):
        fields = [
            self[f'property_{prop}']
            for prop in self.place.settings.work_properties.keys()
            if prop not in self.no_render_properties
        ]
        fields.sort(key=lambda f: f.label)
        return fields

    def save(self, commit=True):
        work = super(WorkForm, self).save(commit)
        self.save_properties()
        self.save_publication_document()
        self.save_commencement()
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

        elif pub_doc_file:
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


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        exclude = ('document_xml', 'created_at', 'updated_at', 'created_by_user', 'updated_by_user',)


class UserEditorForm(forms.ModelForm):
    first_name = forms.CharField(label='First name')
    last_name = forms.CharField(label='Last name')

    class Meta:
        model = Editor
        fields = ('country',)

    def save(self, commit=True):
        super(UserEditorForm, self).save()
        self.instance.user.first_name = self.cleaned_data['first_name']
        self.instance.user.last_name = self.cleaned_data['last_name']
        self.instance.user.save()


class UserSignupForm(SignupForm):
    first_name = forms.CharField(required=True, max_length=30, label='First name')
    last_name = forms.CharField(required=True, max_length=30, label='Last name')
    country = forms.ModelChoiceField(required=True, queryset=Country.objects, label='Country', empty_label=None)
    captcha = ReCaptchaField()
    accepted_terms = forms.BooleanField(required=True, initial=False, error_messages={
        'required': 'Please accept the Terms of Use.',
    })
    signup_enabled = settings.ACCOUNT_SIGNUP_ENABLED

    def clean(self):
        if not self.signup_enabled:
            raise forms.ValidationError("Creating new accounts is currently not allowed.")
        return super(UserSignupForm, self).clean()

    def save(self, request):
        user = super(UserSignupForm, self).save(request)
        user.editor.accepted_terms = True
        user.editor.country = self.cleaned_data['country']
        user.editor.save()
        return user


class BatchCreateWorkForm(forms.Form):
    spreadsheet_url = forms.URLField(required=True, validators=[
        URLValidator(
            schemes=['https'],
            regex='^https:\/\/docs.google.com\/spreadsheets\/d\/\S+\/',
            message="Please enter a valid Google Sheets URL, such as https://docs.google.com/spreadsheets/d/ABCXXX/", code='bad')
    ])
    sheet_name = forms.ChoiceField(required=False, choices=[])
    workflow = forms.ModelChoiceField(queryset=Workflow.objects, empty_label="(None)", required=False)


class ImportDocumentForm(forms.Form):
    file = forms.FileField()
    language = forms.ModelChoiceField(Language.objects)
    expression_date = forms.DateField()
    page_nums = forms.CharField(required=False)
    # options as JSON data
    options = forms.CharField(required=False)

    def clean_options(self):
        val = self.cleaned_data['options']
        try:
            return json.loads(val or '{}')
        except ValueError:
            raise forms.ValidationError("Invalid json data")


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title', 'description', 'work', 'document', 'labels', 'workflows')

    labels = forms.ModelMultipleChoiceField(queryset=TaskLabel.objects, widget=forms.CheckboxSelectMultiple,
                                            required=False)
    workflows = forms.ModelMultipleChoiceField(queryset=Workflow.objects, required=False)

    def __init__(self, country, locality, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country = country
        self.locality = locality
        self.fields['workflows'].queryset = self.fields['workflows'].queryset.\
            filter(country=self.country, locality=self.locality, closed=False).order_by('title')


class TaskFilterForm(forms.Form):
    labels = forms.ModelMultipleChoiceField(queryset=TaskLabel.objects, to_field_name='slug')
    state = forms.MultipleChoiceField(choices=((x, x) for x in Task.STATES + ('assigned',)))
    format = forms.ChoiceField(choices=[('columns', 'columns'), ('list', 'list')])
    assigned_to = forms.ModelMultipleChoiceField(queryset=User.objects)
    submitted_by = forms.ModelMultipleChoiceField(queryset=User.objects)
    type = forms.MultipleChoiceField(choices=Task.CODES)
    country = forms.ModelMultipleChoiceField(queryset=Country.objects)

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super(TaskFilterForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(editor__permitted_countries=self.country).order_by('first_name', 'last_name').all()
        self.fields['submitted_by'].queryset = self.fields['assigned_to'].queryset

    def filter_queryset(self, queryset):
        if self.cleaned_data.get('country'):
            queryset = queryset.filter(country__in=self.cleaned_data['country'])

        if self.cleaned_data.get('type'):
            queryset = queryset.filter(code__in=self.cleaned_data['type'])

        if self.cleaned_data.get('labels'):
            queryset = queryset.filter(labels__in=self.cleaned_data['labels'])

        if self.cleaned_data.get('state'):
            if 'assigned' in self.cleaned_data['state']:
                queryset = queryset.filter(state__in=self.cleaned_data['state'] + ['open'])
                if 'open' not in self.cleaned_data['state']:
                    queryset = queryset.exclude(state='open', assigned_to=None)
            elif 'pending_review' in self.cleaned_data['state']:
                queryset = queryset.filter(state__in=self.cleaned_data['state']).filter(assigned_to=None) | \
                           queryset.filter(state='pending_review')
            else:
                queryset = queryset.filter(state__in=self.cleaned_data['state']).filter(assigned_to=None)

        if self.cleaned_data.get('assigned_to'):
            queryset = queryset.filter(assigned_to__in=self.cleaned_data['assigned_to'])

        if self.cleaned_data.get('submitted_by'):
            queryset = queryset.filter(state__in=['pending_review', 'closed'])\
                .filter(submitted_by_user__in=self.cleaned_data['submitted_by'])

        return queryset

    def data_as_url(self):
        return urllib.parse.urlencode(self.cleaned_data, 'utf-8')


class WorkFilterForm(forms.Form):
    q = forms.CharField()
    stub = forms.ChoiceField(choices=[('', 'Exclude stubs'), ('only', 'Only stubs'), ('all', 'Everything')])
    status = forms.MultipleChoiceField(choices=[('published', 'published'), ('draft', 'draft')], initial=['published', 'draft'])
    sortby = forms.ChoiceField(choices=[('-updated_at', '-updated_at'), ('updated_at', 'updated_at'), ('title', 'title'), ('-title', '-title'), ('frbr_uri', 'frbr_uri')])
    # assent date filter
    assent = forms.ChoiceField(choices=[('', 'Any'), ('no', 'Not assented to'), ('yes', 'Assented to'), ('range', 'Assented to between...')])
    assent_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    assent_date_end = forms.DateField(input_formats=['%Y-%m-%d'])
    # publication date filter
    publication = forms.ChoiceField(choices=[('', 'Any'), ('no', 'No publication date'), ('yes', 'Published'), ('range', 'Published between...')])
    publication_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    publication_date_end = forms.DateField(input_formats=['%Y-%m-%d'])
    # amendment date filter
    amendment = forms.ChoiceField(choices=[('', 'Any'), ('no', 'Not amended'), ('yes', 'Amended'), ('range', 'Amended between...')])
    amendment_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    amendment_date_end = forms.DateField(input_formats=['%Y-%m-%d'])
    # commencement date filter
    commencement = forms.ChoiceField(choices=[('', 'Any'), ('no', 'Not commenced'), ('date_unknown', 'Commencement date unknown'), ('yes', 'Commenced'), ('partial', 'Partially commenced'), ('multiple', 'Multiple commencements'), ('range', 'Commenced between...')])
    commencement_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    commencement_date_end = forms.DateField(input_formats=['%Y-%m-%d'])
    # repealed work filter
    repeal = forms.ChoiceField(choices=[('', 'Any'), ('no', 'Not repealed'), ('yes', 'Repealed'), ('range', 'Repealed between...')])
    repealed_date_start = forms.DateField(input_formats=['%Y-%m-%d'])
    repealed_date_end = forms.DateField(input_formats=['%Y-%m-%d'])
    # primary work filter
    primary_subsidiary = forms.ChoiceField(choices=[('', 'Primary and subsidiary works'), ('primary', 'Primary works only'), ('subsidiary', 'Subsidiary works only')])
    completeness = forms.ChoiceField(choices=[('', 'Complete and incomplete works'), ('complete', 'Complete works only'), ('incomplete', 'Incomplete works only')])
    taxonomies = forms.ModelMultipleChoiceField(
        queryset=VocabularyTopic.objects
            .select_related('vocabulary')
            .order_by('vocabulary__title', 'level_1', 'level_2'))

    advanced_filters = ['assent', 'publication', 'repeal', 'amendment', 'commencement',
                        'primary_subsidiary', 'taxonomies', 'completeness', 'status']

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super(WorkFilterForm, self).__init__(*args, **kwargs)
        self.fields['subtype'] = forms.ChoiceField(choices=[('', 'All types'), ('acts_only', 'Acts only')] + [(s.abbreviation, s.name) for s in Subtype.objects.all()])

    def data_as_url(self):
        return urllib.parse.urlencode(self.cleaned_data, 'utf-8')

    def show_advanced_filters(self):
        # Should we show the advanced options box by default?
        # true if there is a value set, and it's not the initial value
        def is_set(a):
            return (self.cleaned_data.get(a) and
                    (not self.fields.get(a).initial or
                     self.fields.get(a).initial != self.cleaned_data.get(a)))

        return any(is_set(a) for a in self.advanced_filters)

    def filter_queryset(self, queryset):
        if self.cleaned_data.get('q'):
            queryset = queryset.filter(Q(title__icontains=self.cleaned_data['q']) | Q(frbr_uri__icontains=self.cleaned_data['q']))

        if not self.cleaned_data.get('stub'):
            queryset = queryset.filter(stub=False)
        elif self.cleaned_data.get('stub') == 'only':
            queryset = queryset.filter(stub=True)

        if self.cleaned_data.get('status'):
            if self.cleaned_data['status'] == ['draft']:
                queryset = queryset.filter(document__draft=True)            
            elif self.cleaned_data['status'] == ['published']:
                queryset = queryset.filter(document__draft=False)

        if self.cleaned_data.get('sortby'):
            queryset = queryset.order_by(self.cleaned_data.get('sortby'))        
        
        # filter by subtype indicated on frbr_uri
        if self.cleaned_data.get('subtype'):
            if self.cleaned_data['subtype'] == 'acts_only':
                queryset = queryset.filter(frbr_uri__regex=r'.\/act\/\d{4}\/\w+')
            else:
                queryset = queryset.filter(frbr_uri__contains='/act/%s/' % self.cleaned_data['subtype'])

        if self.cleaned_data.get('taxonomies'):
            queryset = queryset.filter(taxonomies__in=self.cleaned_data.get('taxonomies'))

        # Advanced filters

        # filter by assent date range
        if self.cleaned_data.get('assent') == 'yes':
            queryset = queryset.filter(assent_date__isnull=False)
        elif self.cleaned_data.get('assent') == 'no':
            queryset = queryset.filter(assent_date__isnull=True)
        elif self.cleaned_data.get('assent') == 'range':
            if self.cleaned_data.get('assent_date_start') and self.cleaned_data.get('assent_date_end'):
                start_date = self.cleaned_data['assent_date_start']
                end_date = self.cleaned_data['assent_date_end']
                queryset = queryset.filter(assent_date__range=[start_date, end_date]).order_by('-assent_date')

        # filter by publication date range
        if self.cleaned_data.get('publication') == 'yes':
            queryset = queryset.filter(publication_date__isnull=False)
        elif self.cleaned_data.get('publication') == 'no':
            queryset = queryset.filter(publication_date__isnull=True)
        elif self.cleaned_data.get('publication') == 'range':
            if self.cleaned_data.get('publication_date_start') and self.cleaned_data.get('publication_date_end'):
                start_date = self.cleaned_data['publication_date_start']
                end_date = self.cleaned_data['publication_date_end']
                queryset = queryset.filter(publication_date__range=[start_date, end_date]).order_by('-publication_date')

        # filter by repeal date
        if self.cleaned_data.get('repeal') == 'yes':
            queryset = queryset.filter(repealed_date__isnull=False)
        elif self.cleaned_data.get('repeal') == 'no':
            queryset = queryset.filter(repealed_date__isnull=True)
        elif self.cleaned_data.get('repeal') == 'range':
            if self.cleaned_data.get('repealed_date_start') and self.cleaned_data.get('repealed_date_end'):
                start_date = self.cleaned_data['repealed_date_start']
                end_date = self.cleaned_data['repealed_date_end']
                queryset = queryset.filter(repealed_date__range=[start_date, end_date]).order_by('-repealed_date')

        # filter by amendment date
        if self.cleaned_data.get('amendment') == 'yes':
            queryset = queryset.filter(amendments__date__isnull=False)
        elif self.cleaned_data.get('amendment') == 'no':
            queryset = queryset.filter(amendments__date__isnull=True)
        elif self.cleaned_data.get('amendment') == 'range':
            if self.cleaned_data.get('amendment_date_start') and self.cleaned_data.get('amendment_date_end'):
                start_date = self.cleaned_data['amendment_date_start']
                end_date = self.cleaned_data['amendment_date_end']
                queryset = queryset.filter(amendments__date__range=[start_date, end_date]).order_by('-amendments__date')

        # filter by primary work
        if self.cleaned_data.get('primary_subsidiary'):
            if self.cleaned_data['primary_subsidiary'] == 'primary':
                queryset = queryset.filter(parent_work__isnull=True)
            elif self.cleaned_data['primary_subsidiary'] == 'subsidiary':
                queryset = queryset.filter(parent_work__isnull=False)

        # filter by work completeness
        if self.cleaned_data.get('completeness'):
            if self.cleaned_data['completeness'] == 'complete':
                queryset = queryset.filter(metrics__p_breadth_complete__exact=100)
            elif self.cleaned_data['completeness'] == 'incomplete':
                queryset = queryset.filter(metrics__p_breadth_complete__lt=100)

        # filter by commencement status (last because expensive)
        if self.cleaned_data.get('commencement') == 'yes':
            queryset = queryset.filter(commenced=True)
        elif self.cleaned_data.get('commencement') == 'no':
            queryset = queryset.filter(commenced=False)
        elif self.cleaned_data.get('commencement') == 'date_unknown':
            queryset = queryset.filter(commencement_date__isnull=True).filter(commenced=True)
        elif self.cleaned_data.get('commencement') == 'partial':
            # ignore uncommenced works, include works that have any uncommenced provisions
            work_ids = [w.pk for w in queryset if w.commencements.exists() and w.all_uncommenced_provision_ids()]
            queryset = queryset.filter(pk__in=work_ids)
        elif self.cleaned_data.get('commencement') == 'multiple':
            queryset = queryset \
                .annotate(Count('commencements')) \
                .filter(commencements__count__gt=1)
        elif self.cleaned_data.get('commencement') == 'range':
            if self.cleaned_data.get('commencement_date_start') and self.cleaned_data.get('commencement_date_end'):
                start_date = self.cleaned_data['commencement_date_start']
                end_date = self.cleaned_data['commencement_date_end']
                queryset = queryset.filter(commencement_date__range=[start_date, end_date]).order_by('-commencement_date')

        return queryset

    def filter_document_queryset(self, queryset):
        status = self.cleaned_data.get('status')

        if status == ['draft']:
            queryset = queryset.filter(draft=True)
        elif status == ['published']:
            queryset = queryset.filter(draft=False)

        return queryset


class WorkflowFilterForm(forms.Form):
    state = forms.ChoiceField(choices=[('open', 'open'), ('closed', 'closed')])

    def filter_queryset(self, queryset):
        if self.cleaned_data.get('state') == 'open':
            queryset = queryset.filter(closed=False)
        elif self.cleaned_data.get('state') == 'closed':
            queryset = queryset.filter(closed=True)

        return queryset


class BulkTaskUpdateForm(forms.Form):
    tasks = forms.ModelMultipleChoiceField(queryset=Task.objects)
    assigned_to = forms.ModelChoiceField(queryset=User.objects, empty_label='Unassigned', required=False)
    unassign = False

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super(BulkTaskUpdateForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(editor__permitted_countries=self.country).order_by('first_name', 'last_name').all()

    def clean_assigned_to(self):
        user = self.cleaned_data['assigned_to']
        if user and self.country not in user.editor.permitted_countries.all():
            raise forms.ValidationError("That user doesn't have appropriate permissions for {}".format(self.country.name))
        return user

    def clean(self):
        if self.data.get('assigned_to') == '-1':
            del self.errors['assigned_to']
            self.cleaned_data['assigned_to'] = None
            self.unassign = True


class CountryAdminForm(forms.ModelForm):
    italics_terms = SimpleArrayField(forms.CharField(max_length=1024, required=False), delimiter='\n', required=False, widget=forms.Textarea)

    class Meta:
        model = Country
        fields = ('country', 'primary_language', 'italics_terms')

    def clean_italics_terms(self):
        # strip blanks and duplications
        return sorted(list(set(x for x in self.cleaned_data['italics_terms'] if x)))


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


class PlaceSettingsForm(forms.ModelForm):
    class Meta:
        model = PlaceSettings
        fields = ('spreadsheet_url', 'as_at_date', 'styleguide_url', 'no_publication_document_text', 'consolidation_note')

    spreadsheet_url = forms.URLField(required=False, validators=[
        URLValidator(
            schemes=['https'],
            regex='^https:\/\/docs.google.com\/spreadsheets\/d\/\S+\/[\w#=]*',
            message="Please enter a valid Google Sheets URL, such as https://docs.google.com/spreadsheets/d/ABCXXX/", code='bad')
    ])

    def clean_spreadsheet_url(self):
        url = self.cleaned_data.get('spreadsheet_url')
        return re.sub('/[\w#=]*$', '/', url)


class ExplorerForm(forms.Form):
    xpath = forms.CharField(required=True)
    parent = forms.ChoiceField(choices=[('', 'None'), ('1', '1 level'), ('2', '2 levels')], required=False)
    localities = forms.BooleanField(required=False)

    def clean_xpath(self):
        value = self.cleaned_data['xpath']

        try:
            etree.XPath(value)
        except etree.XPathError as e:
            raise ValidationError(str(e))

        return value

    def data_as_url(self):
        return urllib.parse.urlencode(self.cleaned_data, 'utf-8')
