# coding=utf-8
from __future__ import unicode_literals

from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib import messages

from indigo_api.models import Task, Workflow

from indigo_app.views.base import AbstractAuthedIndigoView, PlaceViewBase
from indigo_app.forms import WorkflowForm


class WorkflowViewBase(PlaceViewBase, AbstractAuthedIndigoView):
    tab = 'workflows'


class WorkflowCreateView(WorkflowViewBase, CreateView):
    # permissions
    permission_required = ('indigo_api.add_workflow',)

    js_view = ''

    context_object_name = 'workflow'
    form_class = WorkflowForm
    model = Workflow

    def get_context_data(self, *args, **kwargs):
        context = super(WorkflowCreateView, self).get_context_data(**kwargs)

        context['place_open_tasks'] = self.place.tasks.filter(state__in=Task.OPEN_STATES)

        return context

    def get_form(self, form_class=None):
        form = super(WorkflowCreateView, self).get_form(form_class)

        task_id = self.request.GET.get('task_id')
        if task_id:
            form.initial['task_id'] = int(task_id)

        return form

    def get_form_kwargs(self):
        kwargs = super(WorkflowCreateView, self).get_form_kwargs()

        workflow = Workflow()
        workflow.country = self.country
        workflow.locality = self.locality
        workflow.created_by_user = self.request.user

        kwargs['instance'] = workflow

        return kwargs

    def get_success_url(self):
        return reverse('workflow_detail', kwargs={'place': self.kwargs['place'], 'pk': self.object.pk})


class WorkflowDetailView(WorkflowViewBase, DetailView):
    context_object_name = 'workflow'
    model = Workflow

    def get_context_data(self, *args, **kwargs):
        context = super(WorkflowDetailView, self).get_context_data(**kwargs)

        context['task_groups'] = Task.task_columns(['open', 'pending_review'], self.object.tasks.all())

        # TODO: load from API? filter? exclude closed tasks?
        context['possible_tasks'] = self.country.tasks.exclude(pk__in=[t.id for t in self.object.tasks.all()]).all()

        return context


class WorkflowEditView(WorkflowViewBase, UpdateView):
    # permissions
    permission_required = ('indigo_api.change_workflow',)

    context_object_name = 'workflow'
    form_class = WorkflowForm
    model = Workflow

    def form_valid(self, form):
        self.object.updated_by_user = self.request.user
        return super(WorkflowEditView, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(WorkflowEditView, self).get_context_data(**kwargs)

        context['place_open_tasks'] = self.place.tasks.filter(state__in=Task.OPEN_STATES)

        return context

    def get_success_url(self):
        return reverse('workflow_detail', kwargs={'place': self.kwargs['place'], 'pk': self.object.pk})


class WorkflowAddTasksView(WorkflowViewBase, UpdateView):
    """ A POST-only view that adds tasks to a workflow.
    """
    model = Workflow
    fields = ('tasks',)

    def form_valid(self, form):
        self.object.updated_by_user = self.request.user
        self.object.tasks.add(*(form.cleaned_data['tasks']))
        messages.success(self.request, u"Added %d tasks to this workflow." % len(form.cleaned_data['tasks']))
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('workflow_detail', kwargs={'place': self.kwargs['place'], 'pk': self.object.pk})


class WorkflowListView(WorkflowViewBase, ListView):
    context_object_name = 'workflows'
    paginate_by = 20
    paginate_orphans = 4
    model = Workflow

    def get_queryset(self):
        workflows = self.place.workflows.all()
        return workflows
