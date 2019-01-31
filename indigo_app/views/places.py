# coding=utf-8
import logging
import json
from collections import defaultdict

from django.views.generic import TemplateView
from django.db.models import Count
from django.shortcuts import redirect

from indigo_api.models import Country, Annotation, Task
from indigo_api.serializers import WorkSerializer, DocumentSerializer
from indigo_api.views.works import WorkViewSet
from indigo_api.views.documents import DocumentViewSet

from .base import AbstractAuthedIndigoView, PlaceViewBase


log = logging.getLogger(__name__)


class PlaceListView(AbstractAuthedIndigoView, TemplateView):
    template_name = 'place/list.html'
    js_view = ''

    def dispatch(self, request, **kwargs):
        if Country.objects.count == 1:
            return redirect('place', place=Country.objects.all()[0].place_code)

        return super(PlaceListView, self).dispatch(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PlaceListView, self).get_context_data(**kwargs)

        context['countries'] = Country.objects\
            .prefetch_related('country')\
            .annotate(n_works=Count('works'))\
            .all()

        return context


class PlaceDetailView(PlaceViewBase, AbstractAuthedIndigoView, TemplateView):
    template_name = 'place/detail.html'
    js_view = 'LibraryView'
    tab = 'works'

    def get_context_data(self, **kwargs):
        context = super(PlaceDetailView, self).get_context_data(**kwargs)

        serializer = WorkSerializer(context={'request': self.request}, many=True)
        works = WorkViewSet.queryset.filter(country=self.country, locality=self.locality)
        context['works_json'] = json.dumps(serializer.to_representation(works))

        serializer = DocumentSerializer(context={'request': self.request}, many=True)
        docs = DocumentViewSet.queryset.filter(work__country=self.country, work__locality=self.locality)
        context['documents_json'] = json.dumps(serializer.to_representation(docs))

        # map from document id to count of open annotations
        annotations = Annotation.objects.values('document_id')\
            .filter(closed=False)\
            .filter(document__deleted=False)\
            .annotate(n_annotations=Count('document_id'))\
            .filter(document__work__country=self.country)
        if self.locality:
            annotations = annotations.filter(document__work__locality=self.locality)

        annotations = {x['document_id']: {'n_annotations': x['n_annotations']} for x in annotations}
        context['annotations_json'] = json.dumps(annotations)

        # tasks for place
        tasks = Task.objects.filter(work__country=self.country, work__locality=self.locality)

        # tasks counts per state and per work
        work_tasks = tasks.values('work_id', 'state').annotate(n_tasks=Count('work_id'))
        task_states = defaultdict(dict)
        for row in work_tasks:
            task_states[row['work_id']][row['state']] = row['n_tasks']

        # summarise task counts per work
        work_tasks = {}
        for work_id, states in task_states.iteritems():
            work_tasks[work_id] = {'n_%s_tasks' % s: states.get(s, 0) for s in Task.STATES}
            work_tasks[work_id]['n_tasks'] = sum(states.itervalues())
        context['work_tasks_json'] = json.dumps(work_tasks)

        # tasks counts per state and per document
        doc_tasks = tasks.values('document_id', 'state').annotate(n_tasks=Count('document_id'))
        task_states = defaultdict(dict)
        for row in doc_tasks:
            task_states[row['document_id']][row['state']] = row['n_tasks']

        # summarise task counts per document
        document_tasks = {}
        for doc_id, states in task_states.iteritems():
            document_tasks[doc_id] = {'n_%s_tasks' % s: states.get(s, 0) for s in Task.STATES}
            document_tasks[doc_id]['n_tasks'] = sum(states.itervalues())
        context['document_tasks_json'] = json.dumps(document_tasks)

        work_n_amendments = {x.id: {'n_amendments': x.amendments.count()} for x in works}
        context['work_n_amendments_json'] = json.dumps(work_n_amendments)

        return context
