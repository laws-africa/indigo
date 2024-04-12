from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', views.CountryViewSet, basename='country')
router.register(r'taxonomy-topics', views.TaxonomyTopicView, basename='taxonomy_topic')
router.register(r'(?P<frbr_uri>akn/[a-z]{2}[-/].*)/toc', views.PublishedDocumentTOCView, basename='published-document-toc'),
router.register(r'(?P<frbr_uri>akn/[a-z]{2}[-/].*)/commencements', views.PublishedDocumentCommencementsView, basename='published-document-commencements'),
router.register(r'(?P<frbr_uri>akn/[a-z]{2}[-/].*)/timeline', views.PublishedDocumentTimelineView, basename='published-document-timeline'),
router.register(r'(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media', views.PublishedDocumentMediaView, basename='published-document-media'),

urlpatterns_base = [
    # Work publication document
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media/publication/(?P<filename>.*)$', views.PublishedDocumentMediaView.as_view({'get': 'get_publication_document'}), name='published-document-publication'),
    # Get a specific media file
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media/(?P<filename>.*)$', views.PublishedDocumentMediaView.as_view({'get': 'get_file'}), name='published-document-file'),
]

urlpatterns = urlpatterns_base + [
    path(r'', include(router.urls)),
    # eg. /akn/za/act/2007/98
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)$', views.PublishedDocumentDetailView.as_view({'get': 'get'}), name='published-document-detail'),
]
