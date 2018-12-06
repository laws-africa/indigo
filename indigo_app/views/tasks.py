# coding=utf-8
from __future__ import unicode_literals
import json

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from .base import AbstractAuthedIndigoView, PlaceBasedView

from indigo_api.models import Task
from indigo_api.serializers import WorkSerializer, DocumentSerializer


class TaskListView(AbstractAuthedIndigoView, PlaceBasedView, ListView):
    # permissions
    permission_required = ('indigo_api.view_work',)
    check_country_perms = False

    context_object_name = 'tasks'
    paginate_by = 16
    paginate_orphans = 4

    tab = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(country=self.country, locality=self.locality).order_by('-created_at')


class TaskDetailView(AbstractAuthedIndigoView, PlaceBasedView, DetailView):
    # permissions
    permission_required = ('indigo_api.view_work',)
    check_country_perms = False

    context_object_name = 'task'
    model = Task
    tab = 'tasks'


class TaskCreateView(AbstractAuthedIndigoView, PlaceBasedView, CreateView):
    # permissions
    permission_required = ('indigo_api.add_work',)
    check_country_perms = False
    js_view = 'TaskEditView'

    context_object_name = 'task'
    fields = ['title', 'work', 'description']
    model = Task

    tab = 'tasks'

    def get_form_kwargs(self):
        kwargs = super(TaskCreateView, self).get_form_kwargs()

        task = Task()
        task.country = self.country
        task.locality = self.locality
        task.created_by = self.request.user

        kwargs['instance'] = task

        return kwargs

    def get_success_url(self):
        return reverse('tasks', kwargs={'place': self.kwargs['place']})


class TaskEditView(AbstractAuthedIndigoView, PlaceBasedView, UpdateView):
    # permissions
    permission_required = ('indigo_api.add_work',)
    check_country_perms = False

    context_object_name = 'task'
    fields = ['title', 'description', 'work']
    model = Task
    tab = 'tasks'

    def get_success_url(self):
        return reverse('task_detail', kwargs={'place': self.kwargs['place'], 'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super(TaskEditView, self).get_context_data(**kwargs)

        work = None
        if self.object.work:
            work = json.dumps(WorkSerializer(instance=self.object.work, context={'request': self.request}).data)
        context['work_json'] = work

        return context


class TaskChangeStateView(AbstractAuthedIndigoView, View, SingleObjectMixin):
    # permissions
    permission_required = ('indigo_api.add_work',)
    check_country_perms = False

    change = None
    http_method_names = [u'post']
    model = Task

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        task.updated_by = self.request.user
        if self.change == 'cancel':
            task.state = 'cancelled'
            messages.success(request, u"Task '%s' has been cancelled" % task.title)
        if self.change == 'reopen':
            task.state = 'open'
            messages.success(request, u"Task '%s' has been reopened" % task.title)
        if self.change == 'submit':
            task.state = 'pending'
            messages.success(request, u"Task '%s' has been submitted for review" % task.title)
        if self.change == 'done':
            task.state = 'closed'
            messages.success(request, u"Task '%s' has been closed" % task.title)
        task.save()

        return redirect('task_detail', place=self.kwargs['place'], pk=self.kwargs['pk'])
