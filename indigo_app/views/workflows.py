# coding=utf-8
from __future__ import unicode_literals

from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView

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


class WorkflowListView(WorkflowViewBase, ListView):
    pass
