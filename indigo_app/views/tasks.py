# coding=utf-8
from __future__ import unicode_literals
import json

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import QueryDict
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from django_fsm import has_transition_perm

from indigo_api.models import Task, Work, TaskLabel
from indigo_api.serializers import WorkSerializer, DocumentSerializer

from indigo_app.views.base import AbstractAuthedIndigoView, PlaceViewBase
from indigo_app.forms import TaskForm, TaskFilterForm


class TaskViewBase(PlaceViewBase, AbstractAuthedIndigoView):
    tab = 'tasks'


class TaskListView(TaskViewBase, ListView):
    # permissions
    permission_required = ('indigo_api.add_task',)

    context_object_name = 'tasks'
    paginate_by = 20
    paginate_orphans = 4
    model = Task

    def get(self, request, *args, **kwargs):
        # allows us to set defaults on the form
        params = QueryDict(mutable=True)
        params.update(request.GET)

        # initial state
        if not params.get('state'):
            params.setlist('state', ['open', 'pending_review'])

        self.form = TaskFilterForm(params)
        self.form.is_valid()
        return super(TaskListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        tasks = Task.objects.filter(country=self.country, locality=self.locality).order_by('-created_at')
        return self.form.filter_queryset(tasks, frbr_uri=self.request.GET.get('frbr_uri'))

    def get_context_data(self, **kwargs):
        context = super(TaskListView, self).get_context_data(**kwargs)
        context['task_labels'] = TaskLabel.objects.all()
        context['form'] = self.form
        context['frbr_uri'] = self.request.GET.get('frbr_uri')
        return context


class TaskDetailView(TaskViewBase, DetailView):
    # permissions
    permission_required = ('indigo_api.add_task',)

    context_object_name = 'task'
    model = Task

    def get_context_data(self, **kwargs):
        context = super(TaskDetailView, self).get_context_data(**kwargs)
        task = self.object

        if self.request.user.has_perm('indigo_api.change_task'):
            context['change_task_permission'] = True

        if has_transition_perm(task.submit, self):
            context['submit_task_permission'] = True

        if has_transition_perm(task.cancel, self):
            context['cancel_task_permission'] = True

        if has_transition_perm(task.reopen, self):
            context['reopen_task_permission'] = True

        if has_transition_perm(task.unsubmit, self):
            context['unsubmit_task_permission'] = True

        if has_transition_perm(task.close, self):
            context['close_task_permission'] = True

        return context


class TaskCreateView(TaskViewBase, CreateView):
    # permissions
    permission_required = ('indigo_api.add_task',)

    js_view = 'TaskEditView'

    context_object_name = 'task'
    form_class = TaskForm
    model = Task

    def get_form_kwargs(self):
        kwargs = super(TaskCreateView, self).get_form_kwargs()

        task = Task()
        task.country = self.country
        task.locality = self.locality
        task.created_by_user = self.request.user

        if self.request.GET.get('frbr_uri'):
            # pre-load a work
            try:
                work = Work.objects.get(frbr_uri=self.request.GET['frbr_uri'])
                if task.country == work.country and task.locality == work.locality:
                    task.work = work
            except Work.DoesNotExist:
                pass

        kwargs['instance'] = task

        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(TaskCreateView, self).get_context_data(**kwargs)
        task = context['form'].instance

        work = None
        if task.work:
            work = json.dumps(WorkSerializer(instance=task.work, context={'request': self.request}).data)
        context['work_json'] = work

        document = None
        if task.document:
            document = json.dumps(DocumentSerializer(instance=task.document, context={'request': self.request}).data)
        context['document_json'] = document

        context['task_labels'] = TaskLabel.objects.all()

        return context

    def get_success_url(self):
        return reverse('task_detail', kwargs={'place': self.kwargs['place'], 'pk': self.object.pk})


class TaskEditView(TaskViewBase, UpdateView):
    # permissions
    permission_required = ('indigo_api.change_task',)

    context_object_name = 'task'
    form_class = TaskForm
    model = Task

    def form_valid(self, form):
        self.object.updated_by_user = self.request.user
        return super(TaskEditView, self).form_valid(form)

    def get_success_url(self):
        return reverse('task_detail', kwargs={'place': self.kwargs['place'], 'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super(TaskEditView, self).get_context_data(**kwargs)

        work = None
        if self.object.work:
            work = json.dumps(WorkSerializer(instance=self.object.work, context={'request': self.request}).data)
        context['work_json'] = work

        document = None
        if self.object.document:
            document = json.dumps(DocumentSerializer(instance=self.object.document, context={'request': self.request}).data)
        context['document_json'] = document

        context['task_labels'] = TaskLabel.objects.all()

        return context


class TaskChangeStateView(TaskViewBase, View, SingleObjectMixin):
    # permissions
    permission_required = ('indigo_api.change_task',)

    change = None
    http_method_names = [u'post']
    model = Task

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        user = self.request.user
        potential_changes = {
            'submit': 'submitted',
            'cancel': 'cancelled',
            'reopen': 'reopened',
            'unsubmit': 'unsubmitted',
            'close': 'closed',
        }

        for change, verb in potential_changes.items():
            if self.change == change:
                state_change = getattr(task, change)
                if not has_transition_perm(state_change, self):
                    raise PermissionDenied
                state_change(user)
                messages.success(request, u"Task '%s' has been %s" % (task.title, verb))

        task.save()

        return redirect('task_detail', place=self.kwargs['place'], pk=self.kwargs['pk'])
