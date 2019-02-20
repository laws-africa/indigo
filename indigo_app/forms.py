import json

from django import forms
from django.core.validators import URLValidator
from django.conf import settings
from captcha.fields import ReCaptchaField
from allauth.account.forms import SignupForm

from indigo_app.models import Editor
from indigo_api.models import Document, Country, Language, Work, PublicationDocument, Task, TaskLabel, User, Workflow


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = (
            'title', 'frbr_uri', 'assent_date', 'parent_work', 'commencement_date', 'commencing_work',
            'repealed_by', 'repealed_date', 'publication_name', 'publication_number', 'publication_date',
        )

    publication_document_file = forms.FileField(required=False)
    delete_publication_document = forms.BooleanField(required=False)

    def save(self, commit=True):
        work = super(WorkForm, self).save(commit)
        self.save_publication_document()
        return work

    def save_publication_document(self):
        pub_doc_file = self.cleaned_data['publication_document_file']
        if pub_doc_file:
            try:
                pub_doc = self.instance.publication_document
            except PublicationDocument.DoesNotExist:
                pub_doc = PublicationDocument(work=self.instance)

            pub_doc.file = pub_doc_file
            pub_doc.size = pub_doc_file.size
            # we force a particular filename
            pub_doc.filename = 'publication-document.pdf'
            pub_doc.mime_type = pub_doc_file.content_type

            pub_doc.save()

        if self.cleaned_data['delete_publication_document']:
            try:
                self.instance.publication_document.delete()
            except PublicationDocument.DoesNotExist:
                pass


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
    assigned_to = forms.ModelChoiceField(queryset=User.objects, empty_label='Unassigned', required=False)


class TaskFilterForm(forms.Form):
    labels = forms.ModelMultipleChoiceField(queryset=TaskLabel.objects, to_field_name='slug')
    state = forms.MultipleChoiceField(choices=((x, x) for x in Task.STATES))
    format = forms.ChoiceField(choices=[('columns', 'columns'), ('list', 'list')])

    def filter_queryset(self, queryset, frbr_uri=None):
        if self.cleaned_data.get('labels'):
            queryset = queryset.filter(labels__in=self.cleaned_data['labels'])

        if self.cleaned_data.get('state'):
            queryset = queryset.filter(state__in=self.cleaned_data['state'])

        if frbr_uri:
            queryset = queryset.filter(work__frbr_uri=frbr_uri)

        return queryset


class WorkflowFilterForm(forms.Form):
    state = forms.ChoiceField(choices=[('open', 'open'), ('closed', 'closed')])

    def filter_queryset(self, queryset):
        if self.cleaned_data.get('state') == 'open':
            queryset = queryset.filter(closed=False)
        elif self.cleaned_data.get('state') == 'closed':
            queryset = queryset.filter(closed=True)

        return queryset
