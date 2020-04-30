from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from . import views
from indigo_content_api.v2 import views as v2_views

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', v2_views.CountryViewSet, basename='country')
router.register(r'taxonomies', v2_views.TaxonomyView, basename='taxonomy')

urlpatterns = [
    path('', include(router.urls)),

    # --- public content API ---
    # viewing a specific document identified by FRBR URI fragment,
    # starting with the two-letter country code

    # Document/work media
    # Work publication document
    re_path(r'^(?P<frbr_uri>(akn/)?[a-z]{2}[-/]\S+?)/media/publication/(?P<filename>.*)$', views.PublishedDocumentMediaViewV1.as_view({'get': 'get_publication_document'}), name='published-document-publication'),
    # Get a specific media file
    re_path(r'^(?P<frbr_uri>(akn/)?[a-z]{2}[-/]\S+?)/media/(?P<filename>.*)$', views.PublishedDocumentMediaViewV1.as_view({'get': 'get_file'}), name='published-document-file'),
    # List media for a work
    re_path(r'^(?P<frbr_uri>(akn/)?[a-z]{2}[-/]\S+?)/media\.(?P<format>[a-z0-9]+)$', views.PublishedDocumentMediaViewV1.as_view({'get': 'list'}), name='published-document-media'),
    re_path(r'^(?P<frbr_uri>(akn/)?[a-z]{2}[-/]\S+?)/media$', views.PublishedDocumentMediaViewV1.as_view({'get': 'list'}), name='published-document-media'),

    # Expression details
    # eg. /za/act/2007/98/toc.json
    re_path(r'^(?P<frbr_uri>(akn/)?[a-z]{2}[-/].*)/toc\.(?P<format>[a-z0-9]+)$', views.PublishedDocumentTOCViewV1.as_view({'get': 'get'}), name='published-document-toc'),
    # eg. /za/act/2007/98
    re_path(r'^(?P<frbr_uri>(akn/)?[a-z]{2}[-/].*)$', views.PublishedDocumentDetailViewV1.as_view({'get': 'get'}), name='published-document-detail'),

    re_path(r'^search/(?P<country>[a-z]{2})$', v2_views.PublishedDocumentSearchView.as_view(), name='public-search'),
]
