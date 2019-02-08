# coding=utf-8
from __future__ import unicode_literals

from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib import messages

from indigo_api.models import Task, Workflow

from indigo_app.views.base import AbstractAuthedIndigoView, PlaceViewBase


class WorkflowViewBase(PlaceViewBase, AbstractAuthedIndigoView):
    tab = 'workflows'


class WorkflowCreateView(WorkflowViewBase, CreateView):
    # permissions
    permission_required = ('indigo_api.add_workflow',)

    context_object_name = 'workflow'
    model = Workflow
    fields = ('title', 'description')

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

        tasks = self.object.tasks.all()
        context['has_tasks'] = bool(tasks)
        context['task_groups'] = Task.task_columns(['open', 'pending_review'], tasks)
        context['possible_tasks'] = self.country.tasks.unclosed().exclude(pk__in=[t.id for t in self.object.tasks.all()]).all()

        return context


class WorkflowEditView(WorkflowViewBase, UpdateView):
    # permissions
    permission_required = ('indigo_api.change_workflow',)

    context_object_name = 'workflow'
    model = Workflow
    fields = ('title', 'description')

    def form_valid(self, form):
        self.object.updated_by_user = self.request.user
        return super(WorkflowEditView, self).form_valid(form)

    def get_success_url(self):
        return reverse('workflow_detail', kwargs={'place': self.kwargs['place'], 'pk': self.object.pk})


class WorkflowAddTasksView(WorkflowViewBase, UpdateView):
    """ A POST-only view that adds tasks to a workflow.
    """
    permission_required = ('indigo_api.change_workflow',)
    model = Workflow
    fields = ('tasks',)
    http_method_names = ['post']

    def form_valid(self, form):
        self.object.updated_by_user = self.request.user
        self.object.tasks.add(*(form.cleaned_data['tasks']))
        messages.success(self.request, u"Added %d tasks to this workflow." % len(form.cleaned_data['tasks']))
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('workflow_detail', kwargs={'place': self.kwargs['place'], 'pk': self.object.pk})


class WorkflowRemoveTaskView(WorkflowViewBase, DetailView):
    permission_required = ('indigo_api.change_workflow',)
    http_method_names = ['post']
    model = Workflow

    def post(self, request, task_pk, *args, **kwargs):
        workflow = self.get_object()
        task = get_object_or_404(Task, pk=task_pk)

        workflow.tasks.remove(task)
        messages.success(self.request, u"Removed %s from this workflow." % task.title)

        return redirect('workflow_detail', place=self.kwargs['place'], pk=workflow.pk)


class WorkflowListView(WorkflowViewBase, ListView):
    context_object_name = 'workflows'
    paginate_by = 20
    paginate_orphans = 4
    model = Workflow

    def get_queryset(self):
        workflows = self.place.workflows.all()
        return workflows
