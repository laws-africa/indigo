# coding=utf-8
from __future__ import unicode_literals

from django.views.generic import ListView

from .base import AbstractAuthedIndigoView, PlaceBasedView

from indigo_api.models import Task


class PlaceTasksView(AbstractAuthedIndigoView, PlaceBasedView, ListView):
    model = Task
    js_view = ''
    page_size = 16

    # permissions
    permission_required = ('indigo_api.view_work',)
    check_country_perms = False

    def get_context_data(self, **kwargs):
        context = super(PlaceTasksView, self).get_context_data(**kwargs)

        context['place'] = self.place

        paginator, page, tasks, is_paginated = self.paginate_queryset(
          Task.objects.filter(country=self.country, locality=self.locality), self.page_size
        )
        context.update({
            'paginator': paginator,
            'page': page,
            'tasks': tasks,
            'is_paginated': is_paginated,
        })

        return context
