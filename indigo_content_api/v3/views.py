from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from indigo_api.models import TaxonomyTopic, Work
from indigo_content_api.v2.views import PublishedDocumentDetailView as PublishedDocumentDetailViewV2, ContentAPIBase

from .serializers import PublishedDocumentSerializerV3


class PublishedDocumentDetailViewV3(PublishedDocumentDetailViewV2):
    serializer_class = PublishedDocumentSerializerV3


class TaxonomyTopicPublishedDocumentsView(ContentAPIBase, ListModelMixin, GenericViewSet):
    """ List of work expressions for a taxonomy topic."""
    filter_backends = PublishedDocumentDetailViewV3.filter_backends
    filterset_fields = PublishedDocumentDetailViewV3.filterset_fields

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
        works = Work.objects.filter(taxonomy_topics__path__startswith=self.taxonomy_topic.path).distinct("pk")
        queryset = queryset.filter(work__in=works)
        return super().filter_queryset(queryset)
