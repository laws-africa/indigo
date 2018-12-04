# coding=utf-8
from __future__ import unicode_literals

from django.views.generic import ListView

from .base import AbstractAuthedIndigoView, PlaceBasedView

from indigo_api.models import Task


class TaskListView(AbstractAuthedIndigoView, PlaceBasedView, ListView):
    # permissions
    permission_required = ('indigo_api.view_work',)
    check_country_perms = False

    context_object_name = 'tasks'
    paginate_by = 16
    paginate_orphans = 4

    def get_queryset(self):
        return Task.objects.filter(country=self.country, locality=self.locality).order_by('-created_at')
