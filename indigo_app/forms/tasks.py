from urllib.parse import urlparse

import requests
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.http import QueryDict

from indigo_api.models import Task, TaskLabel, Country, TaskFile, Work
from indigo_app.forms.works import WorkFilterForm, NegatableModelMultipleChoiceField


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
    labels = NegatableModelMultipleChoiceField(label=_("Labels"), queryset=TaskLabel.objects, to_field_name='slug')
    state = forms.MultipleChoiceField(label=_('State'), choices=Task.SIMPLE_STATE_CHOICES)
    assigned_to = forms.MultipleChoiceField(label=_('Assigned to'), choices=[])
    submitted_by = NegatableModelMultipleChoiceField(label=_('Submitted by'), queryset=User.objects)
    type = forms.MultipleChoiceField(label=_('Task type'), choices=Task.CODES)
    sortby = forms.ChoiceField(choices=[
        ('-created_at', _('Created at (newest first)')), ('created_at', _('Created at (oldest first)')),
        ('-updated_at', _('Updated at (newest first)')), ('updated_at', _('Updated at (oldest first)')),
    ])

    def __init__(self, country, locality, data, *args, **kwargs):
        # allows us to set defaults on the form
        params = QueryDict(mutable=True)
        params.update(data)

        # initial state
        if not params.get('state'):
            params.setlist('state', ['open', 'pending_review'])
        if not params.get('sortby'):
            params.setlist('sortby', ['-updated_at'])

        super().__init__(country, params, *args, **kwargs)

        # ensure assigned_to supports unassigned
        users = User.objects.all()
        self.fields['assigned_to'].choices = (
            [
                ('0', _('(Not assigned)')),
                ('-0', _('(Not assigned)')),
            ] + [
                (str(u.pk), u.username)
                for u in users
            ] + [
                (f'-{u.pk}', u.username)
                for u in users
            ]
        )

        self.locality = locality
        if country:
            self.works_queryset = Work.objects.filter(country=country, locality=locality)
        else:
            self.works_queryset = Work.objects.all()

    def filter_queryset(self, queryset, exclude=None):
        if queryset.model is Work:
            return super().filter_queryset(queryset, exclude=exclude)

        if exclude != "place":
            q = Q()
            for place in self.cleaned_data.get('place', []):
                country, locality = Country.get_country_locality(place)
                q |= Q(country=country, locality=locality)
            queryset = queryset.filter(q)

        if exclude != 'type':
            if self.cleaned_data.get('type'):
                queryset = self.apply_values_filter(self.cleaned_data["type"], queryset, "code")

        if exclude != 'labels':
            if self.cleaned_data.get('labels'):
                queryset = self.apply_model_choices_filter(self.cleaned_data["labels"], queryset, "labels")

        if exclude != 'state':
            if self.cleaned_data.get('state'):
                queryset = self.apply_values_filter(self.cleaned_data["state"], queryset, "state")

        if exclude != 'assigned_to':
            if self.cleaned_data.get('assigned_to'):
                queryset = self.apply_assigned_to_filter(self.cleaned_data["assigned_to"], queryset)

        if exclude != 'submitted_by':
            if self.cleaned_data.get('submitted_by'):
                queryset = self.apply_model_choices_filter(self.cleaned_data["submitted_by"], queryset, "submitted_by_user")

        if exclude != 'taxonomy_topic':
            if self.cleaned_data.get('taxonomy_topic'):
                queryset = queryset.filter(work__taxonomy_topics__in=self.cleaned_data['taxonomy_topic'])

        if self.cleaned_data.get('sortby'):
            queryset = queryset.order_by(self.cleaned_data['sortby'])

        works_queryset = super().filter_queryset(self.works_queryset, exclude=exclude)
        queryset = queryset.filter(Q(work__in=works_queryset) | Q(work__isnull=True))

        return queryset

    def apply_assigned_to_filter(self, values, queryset):
        # this is the same as the default apply_values_filter, but we need to handle unassigned
        values = self.cleaned_data['assigned_to']
        includes = [x for x in values if not x.startswith('-')]
        excludes = [x[1:] for x in values if x.startswith('-')]

        def make_q(items):
            q = Q(assigned_to__in=items)
            # unassigned
            if '0' in items:
                q |= Q(assigned_to__isnull=True)
            return q

        if includes:
            queryset = queryset.filter(make_q(includes))

        if excludes:
            queryset = queryset.exclude(make_q(excludes))

        return queryset

    def task_facets(self, queryset, places_toc):
        facets = []
        self.facet_state(facets, queryset)
        self.facet_assigned_to(facets, queryset)
        self.facet_task_type(facets, queryset)
        self.facet_labels(facets, queryset)
        self.facet_submitted_by(facets, queryset)
        self.facet_place(places_toc, queryset)
        return facets

    def facet_labels(self, facets, qs):
        qs = self.filter_queryset(qs, exclude='labels')
        counts = qs.values('labels__slug').annotate(count=Count('pk')).filter(labels__isnull=False).order_by()
        items = [
            (c['labels__slug'], c['count'])
            for c in counts
        ]
        items.sort(key=lambda x: x[0])
        facets.append(self.facet("labels", "checkbox", items))

    def facet_state(self, facets, qs):
        qs = self.filter_queryset(qs, exclude='state')
        counts = {
            c['state']: c['count']
            for c in qs.values('state').annotate(count=Count('pk')).order_by()
        }
        # we always want to show all states, even if they are zero
        items = [
            (s, counts.get(s, 0))
            for s in Task.STATES
        ]
        facets.append(self.facet("state", "checkbox", items))

        for item in facets[-1].items:
            v = item.value[1:] if item.negated else item.value
            item.icon = f'task-icon-{v} text-{v} small'

    def facet_assigned_to(self, facets, qs):
        qs = self.filter_queryset(qs, exclude='assigned_to')
        counts = qs.values('assigned_to').annotate(count=Count('pk')).order_by()
        items = [
            (str(c['assigned_to'] or '0'), c['count'])
            for c in counts
        ]
        items.sort(key=lambda x: x[0])
        facets.append(self.facet("assigned_to", "checkbox", items))

    def facet_submitted_by(self, facets, qs):
        qs = self.filter_queryset(qs, exclude='submitted_by')
        counts = qs.values('submitted_by_user').annotate(count=Count('pk')).filter(submitted_by_user__isnull=False).order_by()
        items = [
            (c['submitted_by_user'], c['count'])
            for c in counts
        ]
        items.sort(key=lambda x: x[0])
        facets.append(self.facet("submitted_by", "checkbox", items))

    def facet_task_type(self, facets, qs):
        qs = self.filter_queryset(qs, exclude='type')
        count_kwargs = {code: Count('pk', filter=Q(code=code)) for code, _ in Task.CODES}
        counts = qs.aggregate(**count_kwargs)
        items = [
            (code, counts[code])
            for code, _ in Task.CODES
            # don't show zero counts
            if counts.get(code, 0)
        ]
        items.sort(key=lambda x: x[0])
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


class BulkTaskStateChangeForm(forms.Form):
    tasks = forms.ModelMultipleChoiceField(queryset=Task.objects)
