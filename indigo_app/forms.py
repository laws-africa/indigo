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
from django.forms import SelectMultiple
from captcha.fields import ReCaptchaField
from allauth.account.forms import SignupForm

from indigo_app.models import Editor
from indigo_api.models import Document, Country, Language, Work, PublicationDocument, Task, TaskLabel, User, Subtype, \
    Workflow, \
    VocabularyTopic, Commencement, PlaceSettings, TaxonomyTopic


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
    language = forms.ChoiceField(label='Language', choices=settings.LANGUAGES)

    class Meta:
        model = Editor
        fields = ('country', 'language')

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
    taxonomy_topic = forms.CharField()

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

        if self.cleaned_data.get('taxonomy_topic'):
            topic = TaxonomyTopic.objects.filter(slug=self.cleaned_data['taxonomy_topic']).first()
            topics = [topic] + [t for t in topic.get_descendants()]
            queryset = queryset.filter(work__taxonomy_topics__in=topics)

        return queryset

    def data_as_url(self):
        return urllib.parse.urlencode(self.cleaned_data, 'utf-8')


class WorkFilterForm(forms.Form):
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
    status = forms.MultipleChoiceField(choices=[('published', 'published'), ('draft', 'draft')])
    sortby = forms.ChoiceField(choices=[('-created_at', '-created_at'), ('created_at', 'created_at'), ('-updated_at', '-updated_at'), ('updated_at', 'updated_at'), ('title', 'title'), ('-title', '-title')])
    principal = forms.MultipleChoiceField(required=False, choices=[('principal', 'Principal'), ('not_principal', 'Not Principal')])
    tasks = forms.MultipleChoiceField(required=False, choices=[('has_open_tasks', 'Has open tasks'), ('has_unblocked_tasks', 'Has unblocked tasks'), ('has_only_blocked_tasks', 'Has only blocked tasks'), ('no_open_tasks', 'Has no open tasks')])
    primary = forms.MultipleChoiceField(required=False, choices=[('primary', 'Primary'), ('primary_subsidiary', 'Primary with subsidiary'), ('subsidiary', 'Subsidiary')])
    consolidation = forms.MultipleChoiceField(required=False, choices=[('has_consolidation', 'Has consolidation'), ('no_consolidation', 'No Consolidation')])
    documents = forms.MultipleChoiceField(required=False, choices=[('one', 'Has one document'), ('multiple', 'Has multiple documents'), ('none', 'Has no documents'), ('published', 'Has published document(s)'), ('draft', 'Has draft document(s)')])
    taxonomy_topic = forms.CharField()

    advanced_filters = ['assent_date_start', 'publication_date_start', 'repealed_date_start', 'amendment_date_start', 'commencement_date_start']

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super(WorkFilterForm, self).__init__(*args, **kwargs)
        doctypes = [(d[1].lower(), d[0]) for d in
                    settings.INDIGO['DOCTYPES'] +
                    settings.INDIGO['EXTRA_DOCTYPES'].get(self.country.code, [])]
        subtypes = [(s.abbreviation, s.name) for s in Subtype.objects.all()]
        self.fields['subtype'] = forms.MultipleChoiceField(required=False, choices=doctypes + subtypes)

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

    def filter_queryset(self, queryset, exclude=None):

        if self.cleaned_data.get('q'):
            queryset = queryset.filter(Q(title__icontains=self.cleaned_data['q']) | Q(frbr_uri__icontains=self.cleaned_data['q']))

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
                tasks_qs |= Q(tasks__state__in=Task.OPEN_STATES)
            if "has_unblocked_tasks" in tasks_filter:
                tasks_qs |= Q(tasks__state__in=Task.UNBLOCKED_STATES)
            if "has_only_blocked_tasks" in tasks_filter:
                only_blocked_task_ids = queryset.filter(tasks__state=Task.BLOCKED).exclude(tasks__state__in=Task.UNBLOCKED_STATES).values_list('pk', flat=True)
                tasks_qs |= Q(id__in=only_blocked_task_ids)
            if "no_open_tasks" in tasks_filter:
                tasks_qs |= ~Q(tasks__state__in=Task.OPEN_STATES)

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

        # sort by
        if self.cleaned_data.get('sortby'):
            queryset = queryset.order_by(self.cleaned_data.get('sortby'))

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

        # filter by work completeness
        if self.cleaned_data.get('completeness'):
            if self.cleaned_data['completeness'] == 'complete':
                queryset = queryset.filter(metrics__p_breadth_complete__exact=100)
            elif self.cleaned_data['completeness'] == 'incomplete':
                queryset = queryset.filter(metrics__p_breadth_complete__lt=100)

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
        if self.cleaned_data.get('taxonomy_topic'):
            topic = TaxonomyTopic.objects.filter(slug=self.cleaned_data['taxonomy_topic']).first()
            if topic:
                topics = [topic] + [t for t in topic.get_descendants()]
                queryset = queryset.filter(taxonomy_topics__in=topics)

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
        exclude = []

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
        fields = ('spreadsheet_url', 'as_at_date', 'styleguide_url', 'no_publication_document_text',
                  'consolidation_note', 'is_consolidation', 'uses_chapter', 'publication_date_optional')

    spreadsheet_url = forms.URLField(required=False, validators=[
        URLValidator(
            schemes=['https'],
            regex='^https:\/\/docs.google.com\/spreadsheets\/d\/\S+\/[\w#=]*',
            message="Please enter a valid Google Sheets URL, such as https://docs.google.com/spreadsheets/d/ABCXXX/", code='bad')
    ])

    def clean_spreadsheet_url(self):
        url = self.cleaned_data.get('spreadsheet_url')
        return re.sub('/[\w#=]*$', '/', url)


class PlaceUsersForm(forms.Form):
    # make choices a lambda so that it's evaluated at runtime, not import time
    choices = lambda: [(u.id, (u.get_full_name() or u.username)) for u in User.objects.filter(badges_earned__slug='editor')]
    users = forms.MultipleChoiceField(choices=choices, label="Users with edit permissions", required=False, widget=forms.CheckboxSelectMultiple)


class ExplorerForm(forms.Form):
    xpath = forms.CharField(required=True)
    parent = forms.ChoiceField(choices=[('', 'None'), ('1', '1 level'), ('2', '2 levels')], required=False)
    localities = forms.BooleanField(required=False)
    global_search = forms.BooleanField(required=False)

    def clean_xpath(self):
        value = self.cleaned_data['xpath']

        try:
            etree.XPath(value)
        except etree.XPathError as e:
            raise ValidationError(str(e))

        return value

    def data_as_url(self):
        return urllib.parse.urlencode(self.cleaned_data, 'utf-8')


class WorkBulkActionsForm(forms.Form):
    save = forms.BooleanField()
    works = forms.ModelMultipleChoiceField(queryset=Work.objects, required=True)
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
