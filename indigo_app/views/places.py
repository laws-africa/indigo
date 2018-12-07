# coding=utf-8
import logging
import json

from django.views.generic import TemplateView, RedirectView
from django.urls import reverse

from indigo_api.models import Country
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
    # permissions

    def get_context_data(self, **kwargs):
        context = super(PlaceDetailView, self).get_context_data(**kwargs)

        serializer = WorkSerializer(context={'request': self.request}, many=True)
        works = WorkViewSet.queryset.filter(country=self.country, locality=self.locality)
        context['works_json'] = json.dumps(serializer.to_representation(works))

        serializer = DocumentSerializer(context={'request': self.request}, many=True)
        docs = DocumentViewSet.queryset.filter(work__country=self.country, work__locality=self.locality)
        context['documents_json'] = json.dumps(serializer.to_representation(docs))

        return context
