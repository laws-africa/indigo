import json
import urllib

from django import forms
from django.db.models import Q
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.forms import BaseModelFormSet
from django.forms.formsets import DELETION_FIELD_NAME
from captcha.fields import ReCaptchaField
from allauth.account.forms import SignupForm

from indigo_app.models import Editor
from indigo_api.models import Document, Country, Language, Work, PublicationDocument, Task, TaskLabel, User, Subtype, Workflow, \
    WorkProperty, VocabularyTopic


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = (
            'title', 'frbr_uri', 'assent_date', 'parent_work', 'commencement_date', 'commencing_work',
            'repealed_by', 'repealed_date', 'publication_name', 'publication_number', 'publication_date',
            'publication_document_trusted_url', 'publication_document_size', 'publication_document_mime_type',
            'stub', 'taxonomies',
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

    def save(self, commit=True):
        work = super(WorkForm, self).save(commit)
        self.save_publication_document()
        return work

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


class WorkPropertyForm(forms.ModelForm):
    key = forms.ChoiceField(required=False, choices=[])
    value = forms.CharField(required=False)

    class Meta:
        model = WorkProperty
        fields = ('key', 'value')

    def __init__(self, *args, **kwargs):
        super(WorkPropertyForm, self).__init__(*args, **kwargs)
        self.fields['key'].choices = WorkProperty.KEYS.items()

    def clean(self):
        super(WorkPropertyForm, self).clean()
        if not self.cleaned_data.get('key') or not self.cleaned_data.get('value'):
            self.cleaned_data[DELETION_FIELD_NAME] = True
        return self.cleaned_data


class BaseWorkPropertyFormSet(BaseModelFormSet):
    def setup_extras(self):
        # add extra forms for the properties we don't have yet
        existing = set([p.key for p in self.queryset.all()])
        missing = [key for key in WorkProperty.KEYS.keys() if key not in existing]
        self.extra = len(missing)
        self.initial_extra = [{'key': key} for key in missing]

    def keys_and_forms(self):
        # (value, label) pairs sorted by label
        keys = sorted(WorkProperty.KEYS.items(), key=lambda x: x[1])
        forms_by_key = {f['key'].value(): f for f in self.forms}
        return [{
            'key': val,
            'label': label,
            'form': forms_by_key[val],
        } for val, label in keys]

    def clean(self):
        keys = set()
        for form in self.forms:
            key = form.cleaned_data.get('key')
            if key:
                if key in keys:
                    form.add_error(None, ValidationError("Property '{}' is specified more than once.".format(key)))
                else:
                    keys.add(key)


WorkPropertyFormSet = forms.modelformset_factory(WorkProperty, form=WorkPropertyForm, formset=BaseWorkPropertyFormSet, can_delete=True)


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
    workflows = forms.ModelMultipleChoiceField(queryset=Workflow.objects, widget=forms.CheckboxSelectMultiple,
                                               required=False)


class TaskFilterForm(forms.Form):
    labels = forms.ModelMultipleChoiceField(queryset=TaskLabel.objects, to_field_name='slug')
    state = forms.MultipleChoiceField(choices=((x, x) for x in Task.STATES + ('assigned',)))
    format = forms.ChoiceField(choices=[('columns', 'columns'), ('list', 'list')])
    assigned_to = forms.ModelMultipleChoiceField(queryset=User.objects)
    submitted_by = forms.ModelMultipleChoiceField(queryset=User.objects)

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super(TaskFilterForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(editor__permitted_countries=self.country).order_by('first_name', 'last_name').all()
        self.fields['submitted_by'].queryset = self.fields['assigned_to'].queryset

    def filter_queryset(self, queryset):
        if self.cleaned_data.get('labels'):
            queryset = queryset.filter(labels__in=self.cleaned_data['labels'])

        if self.cleaned_data.get('state'):
            if 'assigned' in self.cleaned_data['state']:
                queryset = queryset.filter(state__in=self.cleaned_data['state'] + ['open'])
                if 'open' not in self.cleaned_data['state']:
                    queryset = queryset.exclude(state='open', assigned_to=None)
            else:
                queryset = queryset.filter(state__in=self.cleaned_data['state']).filter(assigned_to=None)

        if self.cleaned_data.get('assigned_to'):
            queryset = queryset.filter(assigned_to__in=self.cleaned_data['assigned_to'])

        if self.cleaned_data.get('submitted_by'):
            queryset = queryset.filter(state__in=['pending_review', 'closed'])\
                .filter(submitted_by_user__in=self.cleaned_data['submitted_by'])

        return queryset


class WorkFilterForm(forms.Form):
    q = forms.CharField()
    stub = forms.ChoiceField(choices=[('excl', 'excl'), ('all', 'all'), ('only', 'only')])
    status = forms.MultipleChoiceField(choices=[('published', 'published'), ('draft', 'draft')])
    subtype = forms.ModelChoiceField(queryset=Subtype.objects.all(), empty_label='All works')
    sortby = forms.ChoiceField(choices=[('-updated_at', '-updated_at'), ('updated_at', 'updated_at'), ('title', 'title'), ('-title', '-title'), ('frbr_uri', 'frbr_uri')])
    taxonomies = forms.ModelMultipleChoiceField(
        queryset=VocabularyTopic.objects
            .select_related('vocabulary')
            .order_by('vocabulary__title', 'level_1', 'level_2'))

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super(WorkFilterForm, self).__init__(*args, **kwargs)

    def data_as_url(self):
        return urllib.urlencode(self.cleaned_data, 'utf-8')

    def filter_queryset(self, queryset):
        if self.cleaned_data.get('q'):
            queryset = queryset.filter(Q(title__icontains=self.cleaned_data['q']) | Q(frbr_uri__icontains=self.cleaned_data['q']))

        if self.cleaned_data.get('stub'):
            if self.cleaned_data['stub'] == 'excl':
                queryset = queryset.filter(stub=False)

            elif self.cleaned_data['stub'] == 'only':
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
            queryset = queryset.filter(frbr_uri__contains='/act/%s/' % self.cleaned_data['subtype'].abbreviation)

        if self.cleaned_data.get('taxonomies'):
            queryset = queryset.filter(taxonomies__in=self.cleaned_data.get('taxonomies'))

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
