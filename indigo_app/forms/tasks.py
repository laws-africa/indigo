from urllib.parse import urlparse

import requests
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils.translation import ugettext_lazy as _

from indigo_api.models import Task, TaskLabel, Country, TaxonomyTopic, TaskFile, Work
from indigo_app.forms.works import WorkFilterForm
from indigo_app.forms.mixins import FormAsUrlMixin


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('code', 'description', 'work', 'document', 'timeline_date', 'labels', 'title')

    title = forms.CharField(required=False)
    labels = forms.ModelMultipleChoiceField(queryset=TaskLabel.objects, required=False)
    timeline_date = forms.DateField(required=False)
    code = forms.ChoiceField(label=_('Type'), choices=[('', _('None'))] + Task.MAIN_CODES, required=False)

    def __init__(self, country, locality, data=None, files=None, *args, **kwargs):
        super().__init__(data, files, *args, **kwargs)
        self.country = country
        self.locality = locality
        self.fields['labels'].choices = [(label.pk, label.title) for label in self.fields['labels'].queryset]
        task = self.instance
        if task and task.work:
            # don't limit the queryset, just the choices, because the work might change (see TaskFormWorkView)
            document_queryset = task.work.expressions()
            self.fields['document'].choices = [('', _('None'))] + [(document.pk, f'{document.expression_date} · { document.language.code } – {document.title}') for document in document_queryset]
        self.input_file_form = TaskFileForm(self.instance, data=data, files=files, prefix='input_file',
                                            instance=task.input_file or TaskFile())
        self.output_file_form = TaskFileForm(self.instance, data=data, files=files, prefix='output_file',
                                             instance=task.output_file or TaskFile())

    def clean_timeline_date(self):
        timeline_date = self.cleaned_data['timeline_date']
        # whether timeline_date is blank or not, override it with the document's if there is one
        document = self.cleaned_data.get('document')
        if document:
            timeline_date = document.expression_date

        return timeline_date

    def clean_title(self):
        title = self.cleaned_data['title']
        # whether title is blank or not, override it with the code if there is one
        code = self.cleaned_data.get('code')
        if code:
            title = dict(Task.MAIN_CODES)[code]

        # title can't be blank if there's no code though (borrowed this from validate on the base Field class)
        if not title:
            raise ValidationError(self.fields['title'].error_messages['required'], code='required')

        return title

    def is_valid(self):
        return super().is_valid() and self.input_file_form.is_valid() and self.output_file_form.is_valid()

    def has_changed(self):
        return super().has_changed() or self.input_file_form.has_changed() or self.output_file_form.has_changed()

    def save(self, commit=True):
        task = super().save(commit=commit)
        if commit and self.input_file_form.has_changed():
            self.input_file_form.save()
            if self.input_file_form.instance:
                self.input_file_form.instance.task_as_input = task
                self.input_file_form.instance.save()
            task.input_file = self.input_file_form.instance
            task.save()
        if commit and self.output_file_form.has_changed():
            self.output_file_form.save()
            if self.output_file_form.instance:
                self.output_file_form.instance.task_as_output = task
                self.output_file_form.instance.save()
            task.output_file = self.output_file_form.instance
            task.save()
        return task


class TaskFileForm(forms.ModelForm):
    class Meta:
        model = TaskFile
        fields = ('url', 'file')

    url = forms.URLField(required=False)
    file = forms.FileField(required=False)
    clear = forms.BooleanField(required=False)

    def __init__(self, task, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].label = _('Input file') if self.prefix == 'input_file' else _('Output file')
        # we don't yet support output file URLs, but this won't hurt anyone
        self.fields['url'].label = _('Input URL') if self.prefix == 'input_file' else _('Output URL')
        self.task = task

    def save(self, commit=True):
        file = self.cleaned_data['file']
        url = self.cleaned_data['url']
        task_file = self.instance
        # save only gets called if there's a change, so we're either updating or deleting the TaskFile
        # either way, we should delete the actual file
        if self.initial.get('file'):
            self.initial.get('file').delete()
        if url:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            filename = urlparse(url).path.split('/')[-1] or url
            task_file.url = url
            task_file.size = len(resp.content)
            task_file.filename = filename
            task_file.mime_type = resp.headers['Content-Type']
        elif file:
            task_file.file = file
            task_file.size = file.size
            task_file.filename = file.name
            task_file.mime_type = file.content_type
        else:
            # if there was a task_file on the task and it's been cleared, delete it and clear the form instance
            if task_file.pk:
                task_file.delete()
            self.instance = None


class TaskEditLabelsForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('labels',)

    labels = forms.ModelMultipleChoiceField(queryset=TaskLabel.objects, required=False)


class TaskFilterForm(WorkFilterForm):
    labels = forms.ModelMultipleChoiceField(label=_("Labels"), queryset=TaskLabel.objects, to_field_name='slug')
    state = forms.MultipleChoiceField(label=_('State'), choices=Task.STATE_CHOICES)
    format = forms.ChoiceField(choices=[('columns', _('columns')), ('list', _('list'))])
    assigned_to = forms.ModelMultipleChoiceField(label=_('Assigned to'), queryset=User.objects)
    submitted_by = forms.ModelMultipleChoiceField(label=_('Submitted by'), queryset=User.objects)
    type = forms.MultipleChoiceField(label=_('Task type'), choices=Task.CODES)
    country = forms.ModelMultipleChoiceField(queryset=Country.objects.select_related('country'))
    taxonomy_topic = forms.ModelMultipleChoiceField(queryset=TaxonomyTopic.objects, to_field_name='slug', required=False)
    sortby = forms.ChoiceField(choices=[
        ('-created_at', _('Created at (newest first)')), ('created_at', _('Created at (oldest first)')),
        ('-updated_at', _('Updated at (newest first)')), ('updated_at', _('Updated at (oldest first)')),
    ])

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super().__init__(self.country, *args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(editor__permitted_countries=self.country).order_by('first_name', 'last_name').all()
        self.fields['submitted_by'].queryset = self.fields['assigned_to'].queryset

    def filter_queryset(self, queryset, exclude=None):
        if queryset.model is Work:
            return super().filter_queryset(queryset, exclude=exclude)

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
            queryset = queryset.filter(work__taxonomy_topics__in=self.cleaned_data['taxonomy_topic'])

        if self.cleaned_data.get('sortby'):
            queryset = queryset.order_by(self.cleaned_data['sortby'])

        work_queryset = super().filter_queryset(Work.objects.all(), exclude=exclude)
        queryset = queryset.filter(work__in=work_queryset)

        return queryset

    def work_facets(self, queryset, taxonomy_toc, places_toc):
        return super().work_facets(Work.objects.all(), taxonomy_toc, places_toc)

    def task_facets(self, queryset):
        facets = []
        self.facet_labels(facets, queryset)
        self.facet_state(facets, queryset)
        self.facet_assigned_to(facets, queryset)
        self.facet_submitted_by(facets, queryset)
        self.facet_task_type(facets, queryset)
        return facets

    def facet_labels(self, facets, qs):
        qs = self.filter_queryset(qs)
        count_kwargs = {label.slug: Count('pk', filter=Q(labels=label)) for label in TaskLabel.objects.all()}
        counts = qs.aggregate(**count_kwargs)

        items = [
            (label.slug, counts.get(label.slug, 0))
            for label in TaskLabel.objects.all()

        ]
        facets.append(self.facet("labels", "checkbox", items))

    def facet_state(self, facets, qs):
        qs = self.filter_queryset(qs)
        count_kwargs = {state: Count('pk', filter=Q(state=state)) for state, _ in Task.STATE_CHOICES}
        counts = qs.aggregate(**count_kwargs)
        items = [
            (state, counts.get(state, 0))
            for state, _ in Task.STATE_CHOICES
        ]
        facets.append(self.facet("state", "checkbox", items))

    def facet_assigned_to(self, facets, qs):
        qs = self.filter_queryset(qs)
        count_kwargs = {str(user.pk): Count('pk', filter=Q(assigned_to=user)) for user in User.objects.filter(editor__permitted_countries=self.country).all()}
        counts = qs.aggregate(**count_kwargs)
        items = [
            (user.pk, counts.get(str(user.pk), 0))
            for user in User.objects.filter(editor__permitted_countries=self.country).order_by('first_name', 'last_name').all()
        ]
        facets.append(self.facet("assigned_to", "checkbox", items))

    def facet_submitted_by(self, facets, qs):
        qs = self.filter_queryset(qs)
        count_kwargs = {str(user.pk): Count('pk', filter=Q(assigned_to=user)) for user in User.objects.filter(editor__permitted_countries=self.country).all()}
        counts = qs.aggregate(**count_kwargs)
        items = [
            (user.pk, counts.get(str(user.pk), 0))
            for user in User.objects.filter(editor__permitted_countries=self.country).order_by('first_name', 'last_name').all()
        ]
        facets.append(self.facet("submitted_by", "checkbox", items))

    def facet_task_type(self, facets, qs):
        qs = self.filter_queryset(qs)
        count_kwargs = {code: Count('pk', filter=Q(code=code)) for code, _ in Task.CODES}
        counts = qs.aggregate(**count_kwargs)
        items = [
            (code, counts.get(code, 0))
            for code, _ in Task.CODES
        ]
        facets.append(self.facet("type", "checkbox", items))


class BulkTaskUpdateForm(forms.Form):
    tasks = forms.ModelMultipleChoiceField(queryset=Task.objects)
    assigned_to = forms.ModelChoiceField(queryset=User.objects, empty_label=_('Unassigned'), required=False)
    unassign = False

    def __init__(self, country, *args, **kwargs):
        self.country = country
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(editor__permitted_countries=self.country).order_by('first_name', 'last_name').all()

    def clean_assigned_to(self):
        user = self.cleaned_data['assigned_to']
        if user and self.country not in user.editor.permitted_countries.all():
            raise forms.ValidationError(_("That user doesn't have appropriate permissions for %(country)s") % {'country': self.country.name})
        return user

    def clean(self):
        if self.data.get('assigned_to') == '-1':
            del self.errors['assigned_to']
            self.cleaned_data['assigned_to'] = None
            self.unassign = True
