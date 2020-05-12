# coding=utf-8
from datetime import timedelta

from actstream import action
from actstream.models import Action, any_stream
from django.contrib import messages
from django.db.models import Count
from django.http import QueryDict
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from indigo_api.models import Task, Workflow

from indigo_app.forms import WorkflowFilterForm, TaskFilterForm
from indigo_app.views.base import AbstractAuthedIndigoView, PlaceViewBase


class WorkflowViewBase(PlaceViewBase, AbstractAuthedIndigoView):
    tab = 'workflows'


class WorkflowCreateView(WorkflowViewBase, CreateView):
    # permissions
    permission_required = ('indigo_api.add_workflow',)

    context_object_name = 'workflow'
    model = Workflow
    fields = ('title', 'description', 'due_date')

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
    threshold = timedelta(seconds=3)
    js_view = 'WorkflowDetailView TaskBulkUpdateView'

    def get(self, request, *args, **kwargs):
        # allows us to set defaults on the form
        params = QueryDict(mutable=True)
        params.update(request.GET)

        # initial state
        if not params.get('state'):
            params.setlist('state', ['open', 'assigned', 'pending_review', 'done', 'cancelled'])
        params.setdefault('format', 'columns')

        self.form = TaskFilterForm(self.country, params)
        self.form.is_valid()

        return super(WorkflowDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(WorkflowDetailView, self).get_context_data(**kwargs)

        # stats
        self.object.n_tasks = self.object.tasks.count()
        self.object.n_done = self.object.tasks.closed().count()
        self.object.pct_done = self.object.n_done / (self.object.n_tasks or 1) * 100.0

        context['form'] = self.form
        tasks = self.form.filter_queryset(Task.objects.filter(workflows=self.object)) \
            .select_related('document__language', 'document__language__language')\
            .defer('document__document_xml', 'document__search_text', 'document__search_vector')\
            .all()

        context['tasks'] = tasks
        context['has_tasks'] = self.object.n_tasks > 0
        context['task_groups'] = Task.task_columns(['open', 'pending_review', 'assigned'], tasks)
        context['possible_tasks'] = Task.objects.filter(country=self.country, locality=self.locality)\
            .unclosed()\
            .exclude(workflows=self.object) \
            .select_related('document__language', 'document__language__language') \
            .defer('document__document_xml', 'document__search_text', 'document__search_vector')\
            .all()

        # warn when submitting task on behalf of another user
        Task.decorate_submission_message(tasks, self)

        Task.decorate_potential_assignees(tasks, self.country)
        Task.decorate_permissions(tasks, self)

        context['may_close'] = not self.object.closed and self.object.n_tasks == self.object.n_done
        context['may_reopen'] = self.object.closed
        stream = any_stream(self.object)
        context['activity_stream'] = self.coalesce_entries(stream)

        return context

    def coalesce_entries(self, stream):
        """ If more than 1 task were added to the workflow at once, rather display something like
        '<User> added <n> tasks to this workflow at <time>'
        """
        activity_stream = []
        added_stash = []
        for i, action in enumerate(stream):
            if i == 0:
                # is the first action an addition?
                if getattr(action, 'verb', None) == 'added':
                    added_stash.append(action)
                else:
                    activity_stream.append(action)

            else:
                # is a subsequent action an addition?
                if getattr(action, 'verb', None) == 'added':
                    # if yes, was the previous action also an addition?
                    prev = stream[i - 1]
                    if getattr(prev, 'verb', None) == 'added':
                        # if yes, did the two actions happen close together?
                        if prev.timestamp - action.timestamp < self.threshold:
                            # if yes, the previous action was added to the stash and
                            # this action should also be added to the stash
                            added_stash.append(action)
                        else:
                            # if not, this action should start a new stash,
                            # but first squash, add and delete the existing stash
                            stash = self.combine(added_stash)
                            activity_stream.append(stash)
                            added_stash = []
                            added_stash.append(action)
                    else:
                        # the previous action wasn't an addition
                        # so this action should start a new stash
                        added_stash.append(action)
                else:
                    # this action isn't an addition, so squash and add the existing stash first
                    # (if it exists) and then add this action
                    if len(added_stash) > 0:
                        stash = self.combine(added_stash)
                        activity_stream.append(stash)
                        added_stash = []
                    activity_stream.append(action)

        return activity_stream

    def combine(self, stash):
        first = stash[0]
        if len(stash) == 1:
            return first
        else:
            action = Action(actor=first.actor, verb='added %d tasks to' % len(stash), action_object=self.object)
            action.timestamp = first.timestamp
            return action


class WorkflowEditView(WorkflowViewBase, UpdateView):
    # permissions
    permission_required = ('indigo_api.change_workflow',)

    context_object_name = 'workflow'
    model = Workflow
    fields = ('title', 'description', 'due_date', 'priority')

    def form_valid(self, form):
        form_valid = super(WorkflowEditView, self).form_valid(form)
        if form_valid:
            workflow = self.object
            workflow.updated_by_user = self.request.user
            action.send(workflow.updated_by_user, verb='updated', action_object=workflow,
                        place_code=workflow.place.place_code)
            messages.success(self.request, "Workflow updated.")
        return form_valid

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
        workflow = self.object
        if workflow.closed:
            messages.error(self.request, "You can't add tasks to a closed workflow.")
            return redirect(self.get_success_url())

        workflow.updated_by_user = self.request.user
        workflow.tasks.add(*(form.cleaned_data['tasks']))

        for task in form.cleaned_data['tasks']:
            action.send(workflow.updated_by_user, verb='added', action_object=task, target=workflow,
                        place_code=workflow.place.place_code)

        messages.success(self.request, "Added %d tasks to this workflow." % len(form.cleaned_data['tasks']))

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
        workflow.updated_by_user = self.request.user
        action.send(workflow.updated_by_user, verb='removed', action_object=task, target=workflow,
                    place_code=workflow.place.place_code)
        messages.success(self.request, "Removed %s from this workflow." % task.title)

        return redirect('workflow_detail', place=self.kwargs['place'], pk=workflow.pk)


class WorkflowCloseView(WorkflowViewBase, DetailView):
    permission_required = ('indigo_api.close_workflow',)
    http_method_names = ['post']
    model = Workflow

    def post(self, request, *args, **kwargs):
        workflow = self.get_object()

        workflow.closed = True
        workflow.updated_by_user = self.request.user
        workflow.save()
        action.send(workflow.updated_by_user, verb='closed', action_object=workflow,
                    place_code=workflow.place.place_code)

        messages.success(self.request, "Workflow \"%s\" closed." % workflow.title)

        return redirect('workflow_detail', place=self.kwargs['place'], pk=workflow.pk)


class WorkflowReopenView(WorkflowViewBase, DetailView):
    permission_required = ('indigo_api.close_workflow',)
    http_method_names = ['post']
    model = Workflow

    def post(self, request, *args, **kwargs):
        workflow = self.get_object()

        workflow.closed = False
        workflow.updated_by_user = self.request.user
        workflow.save()
        action.send(workflow.updated_by_user, verb='reopened', action_object=workflow,
                    place_code=workflow.place.place_code)

        messages.success(self.request, "Workflow \"%s\" reopened." % workflow.title)

        return redirect('workflow_detail', place=self.kwargs['place'], pk=workflow.pk)


class WorkflowDeleteView(WorkflowViewBase, DetailView):
    permission_required = ('indigo_api.delete_workflow',)
    http_method_names = ['post']
    model = Workflow

    def post(self, request, *args, **kwargs):
        workflow = self.get_object()

        workflow.delete()

        messages.success(self.request, "Workflow \"%s\" deleted." % workflow.title)

        return redirect('workflows', place=self.kwargs['place'])


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
        workflows = Workflow.objects.filter(country=self.country, locality=self.locality)
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
            w.task_counts['total'] = sum(x for x in w.task_counts.values())
            w.task_counts['complete'] = w.task_counts.get('cancelled', 0) + w.task_counts.get('done', 0)
            w.task_counts['assigned'] = w.tasks.filter(state='open').exclude(assigned_to=None).count()
            if w.task_counts['assigned'] > 0:
                w.task_counts['open'] -= w.task_counts['assigned']
            w.pct_complete = w.task_counts['complete'] / (w.task_counts['total'] or 1) * 100.0

            w.task_charts = [(s, w.task_counts.get(s, 0), s.replace('_', ' ')) for s in ['open', 'assigned', 'pending_review', 'cancelled']]

        return context
