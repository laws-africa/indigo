from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, viewsets

from indigo_api.models import TaxonomyTopic, Work, Country
from indigo_content_api.v2.views import PublishedDocumentDetailView as PublishedDocumentDetailViewV2, ContentAPIBase

from .serializers import PublishedDocumentSerializerV3
from ..v2.serializers import PlaceSerializer


class PublishedDocumentDetailViewV3(PublishedDocumentDetailViewV2):
    serializer_class = PublishedDocumentSerializerV3


class PlaceViewSet(ContentAPIBase, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """ Places that the content API supports. """
    queryset = Country.objects.prefetch_related('localities', 'country')
    serializer_class = PlaceSerializer
    # these are both for drf-spectacular
    lookup_url_kwarg = 'frbr_uri_code'
    lookup_field = 'code'

    def get_object(self):
        country, locality = Country.get_country_locality(self.kwargs['frbr_uri_code'])
        return locality or country


class PlaceWorkExpressionsView(ContentAPIBase, ListModelMixin, GenericViewSet):
    """ List of work expressions for a place. """
    filter_backends = PublishedDocumentDetailViewV3.filter_backends
    filterset_fields = PublishedDocumentDetailViewV3.filterset_fields
    country = None
    locality = None

    def get_serializer_class(self):
        return PublishedDocumentDetailViewV3.serializer_class

    def list(self, request, *args, **kwargs):
        self.place = self.get_place(kwargs['frbr_uri_code'])
        return super().list(request, *args, **kwargs)

    def get_place(self, code):
        try:
            self.country, self.locality = Country.get_country_locality(code)
            return self.locality or self.country
        except ObjectDoesNotExist:
            raise Http404()

    def get_queryset(self):
        queryset = PublishedDocumentDetailViewV3.queryset\
                .latest_expression() \
                .prefer_language(self.country.primary_language.code) \
                .filter(work__country=self.country, work__locality=self.locality)
        return super().filter_queryset(queryset)


class WorkExpressionsViewSet(ContentAPIBase, ListModelMixin, GenericViewSet):
    """ List of work expressions across all places. """
    filter_backends = PublishedDocumentDetailViewV3.filter_backends
    filterset_fields = PublishedDocumentDetailViewV3.filterset_fields

    def get_serializer_class(self):
        return PublishedDocumentDetailViewV3.serializer_class

    def get_queryset(self):
        return PublishedDocumentDetailViewV3.queryset


class TaxonomyTopicWorkExpressionsView(ContentAPIBase, ListModelMixin, GenericViewSet):
    """ List of work expressions for a taxonomy topic."""
    filter_backends = PublishedDocumentDetailViewV3.filter_backends
    filterset_fields = PublishedDocumentDetailViewV3.filterset_fields
    taxonomy_topic = None

    def get_serializer_class(self):
        return PublishedDocumentDetailViewV3.serializer_class

    def list(self, request, *args, **kwargs):
        self.taxonomy_topic = self.get_taxonomy_topic(kwargs['slug'])
        return super().list(request, *args, **kwargs)

    def get_taxonomy_topic(self, slug):
        obj = get_object_or_404(TaxonomyTopic.objects, slug=slug)
        if not TaxonomyTopic.get_public_root_nodes().filter(pk=obj.get_root().pk).exists():
            # it's not public
            raise Http404()
        return obj

    def get_queryset(self):
        queryset = PublishedDocumentDetailViewV3.queryset
        # when drf-spectacular generates the schema, it doesn't have the taxonomy_topic attribute
        if not getattr(self, 'swagger_fake_view', False):
            works = Work.objects.filter(taxonomy_topics__path__startswith=self.taxonomy_topic.path).distinct("pk")
            queryset = queryset.filter(work__in=works)
        return super().filter_queryset(queryset)
