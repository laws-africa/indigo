# coding=utf-8
from __future__ import unicode_literals
import json

from actstream import action

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import QueryDict
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from django_fsm import has_transition_perm

from indigo_api.models import Task, TaskLabel, User, Work, Workflow
from indigo_api.serializers import WorkSerializer, DocumentSerializer

from indigo_app.views.base import AbstractAuthedIndigoView, PlaceViewBase
from indigo_app.forms import TaskForm, TaskFilterForm


class TaskViewBase(PlaceViewBase, AbstractAuthedIndigoView):
    tab = 'tasks'


class TaskListView(TaskViewBase, ListView):
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
            params.setlist('state', ['open', 'assigned', 'pending_review'])
        params.setdefault('format', 'columns')

        self.form = TaskFilterForm(params)
        self.form.is_valid()

        if self.form.cleaned_data['format'] == 'columns':
            self.paginate_by = 40

        return super(TaskListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        tasks = Task.objects.filter(country=self.country, locality=self.locality).order_by('-updated_at')
        return self.form.filter_queryset(tasks, frbr_uri=self.request.GET.get('frbr_uri'))

    def get_context_data(self, **kwargs):
        context = super(TaskListView, self).get_context_data(**kwargs)
        context['task_labels'] = TaskLabel.objects.all()
        context['form'] = self.form
        context['frbr_uri'] = self.request.GET.get('frbr_uri')
        context['task_groups'] = Task.task_columns(self.form.cleaned_data['state'], context['tasks'])

        return context


class TaskDetailView(TaskViewBase, DetailView):
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

    def form_valid(self, form):
        response_object = super(TaskCreateView, self).form_valid(form)
        task = self.object
        task.workflows = form.cleaned_data.get('workflows')
        for workflow in task.workflows.all():
            action.send(self.request.user, verb='added', action_object=task, target=workflow,
                        place_code=task.place.place_code)
        return response_object

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

        context['place_workflows'] = self.place.workflows.all()

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
        task = self.object
        old_workflows = [wf.id for wf in task.workflows.all()]
        task.updated_by_user = self.request.user
        task.workflows = form.cleaned_data.get('workflows')

        # action signals
        # first, was something changed other than workflows?
        if form.changed_data:
            action.send(self.request.user, verb='updated', action_object=task,
                        place_code=task.place.place_code)
        # then, was the task added to / removed from any workflows?
        new_workflows = [wf.id for wf in task.workflows.all()]
        removed_workflows = set(old_workflows) - set(new_workflows)
        added_workflows = set(new_workflows) - set(old_workflows)
        for workflow in removed_workflows:
            action.send(self.request.user, verb='removed', action_object=task,
                        target=Workflow.objects.get(id=workflow),
                        place_code=task.place.place_code)
        for workflow in added_workflows:
            action.send(self.request.user, verb='added', action_object=task,
                        target=Workflow.objects.get(id=workflow),
                        place_code=task.place.place_code)

        return super(TaskEditView, self).form_valid(form)

    def get_form(self, form_class=None):
        form = super(TaskEditView, self).get_form(form_class)
        form.initial['workflows'] = self.object.workflows.all()
        return form

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
        context['place_workflows'] = self.place.workflows.all()

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
        task.updated_by_user = user

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
                if verb == 'submitted':
                    task.last_assigned_to = task.assigned_to
                    task.assigned_to = None
                    action.send(user, verb=verb, action_object=task,
                                place_code=task.place.place_code)
                    messages.success(request, u"Task '%s' has been submitted for review" % task.title)
                elif verb == 'unsubmitted':
                    assignee = task.last_assigned_to
                    task.assigned_to = assignee
                    if user.id == assignee.id:
                        action.send(user, verb='unsubmitted and picked up', action_object=task,
                                    place_code=task.place.place_code)
                        messages.success(request, u"You have reopened and picked up the task '%s'" % task.title)
                    else:
                        action.send(user, verb='unsubmitted and reassigned', action_object=task,
                                    target=assignee,
                                    place_code=task.place.place_code)
                        messages.success(request, u"Task '%s' has been reopened and reassigned" % task.title)

                else:
                    action.send(user, verb=verb, action_object=task,
                                place_code=task.place.place_code)
                    messages.success(request, u"Task '%s' has been %s" % (task.title, verb))

        task.save()

        return redirect('task_detail', place=self.kwargs['place'], pk=self.kwargs['pk'])


class TaskAssignView(TaskViewBase, View, SingleObjectMixin):
    # permissions
    permission_required = ('indigo_api.change_task',)

    unassign = False
    http_method_names = [u'post']
    model = Task

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        user = self.request.user
        task.updated_by_user = user
        if self.unassign:
            task.assigned_to = None
            action.send(user, verb='unassigned', action_object=task,
                        place_code=task.place.place_code)
            messages.success(request, u"Task '%s' has been unassigned" % task.title)
        else:
            assignee = User.objects.get(id=self.request.POST.get('user_id'))
            if task.country not in assignee.editor.permitted_countries.all():
                raise PermissionDenied
            task.assigned_to = assignee
            if user.id == assignee.id:
                action.send(user, verb='picked up', action_object=task,
                            place_code=task.place.place_code)
                messages.success(request, u"You have picked up the task '%s'" % task.title)
            else:
                action.send(user, verb='assigned', action_object=task,
                            target=assignee,
                            place_code=task.place.place_code)
                messages.success(request, u"Task '%s' has been assigned" % task.title)

        task.save()

        return redirect('task_detail', place=self.kwargs['place'], pk=self.kwargs['pk'])
