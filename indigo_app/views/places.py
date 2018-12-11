# coding=utf-8
import logging
import json

from django.views.generic import TemplateView, RedirectView
from django.urls import reverse
from django.db.models import Count

from indigo_api.models import Country, Annotation, Task
from indigo_api.serializers import WorkSerializer, DocumentSerializer
from indigo_api.views.works import WorkViewSet
from indigo_api.views.documents import DocumentViewSet

from .base import AbstractAuthedIndigoView, PlaceViewBase


log = logging.getLogger(__name__)


class LibraryView(RedirectView):
    """ Redirect the old library view to the new place view.
    """
    permanent = True

    def get_redirect_url(self, country=None):
        place = country

        if not place:
            if self.request.user.is_authenticated():
                place = self.request.user.editor.country.code
            else:
                place = Country.objects.all()[0].code

        return reverse('place', kwargs={'place': place})


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

        # open / pending_review tasks per work
        work_open_tasks = Task.objects.values('work_id')\
            .filter(state=('open' or 'pending_review'))\
            .annotate(n_open_tasks=Count('work_id'))\
            .filter(country=self.country)
        if self.locality:
            work_open_tasks = work_open_tasks.filter(locality=self.locality)

        work_open_tasks = {x['work_id']: {'n_open_tasks': x['n_open_tasks']} for x in work_open_tasks}
        context['work_open_tasks_json'] = json.dumps(work_open_tasks)

        # open / pending_review tasks per document
        document_open_tasks = Task.objects.values('document_id')\
            .filter(state=('open' or 'pending_review'))\
            .annotate(n_open_tasks=Count('document_id'))\
            .filter(document__work__country=self.country)
        if self.locality:
            document_open_tasks = document_open_tasks.filter(document__work__locality=self.locality)

        document_open_tasks = {x['document_id']: {'n_open_tasks': x['n_open_tasks']} for x in document_open_tasks}
        context['document_open_tasks_json'] = json.dumps(document_open_tasks)

        work_n_amendments = {x.id: {'n_amendments': x.amendments.count()} for x in works}
        context['work_n_amendments'] = json.dumps(work_n_amendments)

        return context
