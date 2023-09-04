from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', views.CountryViewSet, basename='country')
router.register(r'taxonomies', views.TaxonomyView, basename='taxonomy')
router.register(r'taxonomy_topics', views.TaxonomyTopicView, basename='taxonomy_topic')


urlpatterns = [
    path(r'', include(router.urls)),

    # --- public content API ---
    # viewing a specific document identified by FRBR URI fragment,
    # starting with the two-letter country code

    # Document/work media
    # Work publication document
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media/publication/(?P<filename>.*)$', views.PublishedDocumentMediaView.as_view({'get': 'get_publication_document'}), name='published-document-publication'),
    # Get a specific media file
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media/(?P<filename>.*)$', views.PublishedDocumentMediaView.as_view({'get': 'get_file'}), name='published-document-file'),
    # List media for a work
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media\.(?P<format>[a-z0-9]+)$', views.PublishedDocumentMediaView.as_view({'get': 'list'}), name='published-document-media'),
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media$', views.PublishedDocumentMediaView.as_view({'get': 'list'}), name='published-document-media'),

    # Expression details
    # eg. /akn/za/act/2007/98/toc.json
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)/toc\.(?P<format>[a-z0-9]+)$', views.PublishedDocumentTOCView.as_view({'get': 'get'}), name='published-document-toc'),
    # eg. /akn/za/act/1991/108/commencements.json; /akn/za/act/1991/108/eng@1991-06-28/commencements.json
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)/commencements\.(?P<format>[a-z0-9]+)$', views.PublishedDocumentCommencementsView.as_view({'get': 'get'}), name='published-document-commencements'),
    # eg. /akn/za/act/1991/108/timeline.json; /akn/za/act/1991/108/eng@1991-06-28/timeline.json
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)/timeline\.(?P<format>[a-z0-9]+)$', views.PublishedDocumentTimelineView.as_view({'get': 'get'}), name='published-document-timeline'),
    # eg. /akn/za/act/2007/98
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)$', views.PublishedDocumentDetailView.as_view({'get': 'get'}), name='published-document-detail'),
]
