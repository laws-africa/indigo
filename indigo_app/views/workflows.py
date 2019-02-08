# coding=utf-8
from __future__ import unicode_literals, division

from django.contrib import messages
from django.db.models import Count
from django.http import QueryDict
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from indigo_api.models import Task, Workflow

from indigo_app.forms import WorkflowFilterForm
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
        context['possible_tasks'] = self.place.tasks.unclosed().exclude(pk__in=[t.id for t in self.object.tasks.all()]).all()

        # stats
        self.object.n_tasks = self.object.tasks.count()
        self.object.n_done = self.object.tasks.closed().count()
        self.object.pct_done = self.object.n_done / (self.object.n_tasks or 1) * 100.0

        context['may_close'] = self.object.n_tasks == self.object.n_done
        context['may_reopen'] = self.object.closed

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


class WorkflowCloseView(WorkflowViewBase, DetailView):
    permission_required = ('indigo_api.close_workflow',)
    http_method_names = ['post']
    model = Workflow

    def post(self, request, *args, **kwargs):
        workflow = self.get_object()

        workflow.closed = True
        workflow.updated_by_user = self.request.user
        workflow.closed_by_user = self.request.user
        workflow.save()

        messages.success(self.request, u"Workflow \"%s\" closed." % workflow.title)

        return redirect('workflows', place=self.kwargs['place'])


class WorkflowReopenView(WorkflowViewBase, DetailView):
    permission_required = ('indigo_api.close_workflow',)
    http_method_names = ['post']
    model = Workflow

    def post(self, request, *args, **kwargs):
        workflow = self.get_object()

        workflow.closed = False
        workflow.updated_by_user = self.request.user
        workflow.save()

        messages.success(self.request, u"Workflow \"%s\" reopened." % workflow.title)

        return redirect('workflow_detail', place=self.kwargs['place'], pk=workflow.pk)


class WorkflowListView(WorkflowViewBase, ListView):
    context_object_name = 'workflows'
    paginate_by = 20
    paginate_orphans = 4
    model = Workflow

    def get(self, request, *args, **kwargs):
        # allows us to set defaults on the form
        params = QueryDict(mutable=True)
        params.update(request.GET)

        # initial state
        params.setdefault('state', 'open')

        self.form = WorkflowFilterForm(params)
        self.form.is_valid()

        return super(WorkflowListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        workflows = self.place.workflows.filter()
        return self.form.filter_queryset(workflows)

    def get_context_data(self, **kwargs):
        context = super(WorkflowListView, self).get_context_data(**kwargs)

        context['form'] = self.form

        workflows = context['workflows']

        # count tasks by state
        task_stats = Workflow.objects\
            .values('id', 'tasks__state')\
            .annotate(n_tasks=Count('tasks__id'))\
            .filter(id__in=[w.id for w in workflows])

        for w in workflows:
            w.task_counts = {s['tasks__state']: s['n_tasks'] for s in task_stats if s['id'] == w.id}
            w.task_counts['total'] = sum(x for x in w.task_counts.itervalues())
            w.task_counts['complete'] = w.task_counts.get('cancelled', 0) + w.task_counts.get('done', 0)
            w.pct_complete = w.task_counts['complete'] / (w.task_counts['total'] or 1) * 100.0

            w.task_charts = [(s, w.task_counts.get(s, 0)) for s in ['open', 'pending_review', 'cancelled']]

        return context
