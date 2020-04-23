from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', views.CountryViewSet, basename='country')
router.register(r'taxonomies', views.TaxonomyView, basename='taxonomy')

urlpatterns = [
    url(r'^', include(router.urls)),

    # --- public content API ---
    # viewing a specific document identified by FRBR URI fragment,
    # starting with the two-letter country code

    # Document/work media
    # Work publication document
    url(r'^(?P<frbr_uri>[a-z]{2}[-/]\S+?)/media/publication/(?P<filename>.*)$', views.PublishedDocumentMediaView.as_view({'get': 'get_publication_document'}), name='published-document-publication'),
    # Get a specific media file
    url(r'^(?P<frbr_uri>[a-z]{2}[-/]\S+?)/media/(?P<filename>.*)$', views.PublishedDocumentMediaView.as_view({'get': 'get_file'}), name='published-document-file'),
    # List media for a work
    url(r'^(?P<frbr_uri>[a-z]{2}[-/]\S+?)/media\.(?P<format>[a-z0-9]+)$', views.PublishedDocumentMediaView.as_view({'get': 'list'}), name='published-document-media'),
    url(r'^(?P<frbr_uri>[a-z]{2}[-/]\S+?)/media$', views.PublishedDocumentMediaView.as_view({'get': 'list'}), name='published-document-media'),

    # Expression details
    # eg. /za/act/2007/98/toc.json
    url(r'^(?P<frbr_uri>[a-z]{2}[-/].*)/toc\.(?P<format>[a-z0-9]+)$', views.PublishedDocumentTOCView.as_view({'get': 'get'}), name='published-document-toc'),
    # eg. /za/act/2007/98
    url(r'^(?P<frbr_uri>[a-z]{2}[-/].*)$', views.PublishedDocumentDetailView.as_view({'get': 'get'}), name='published-document-detail'),

    url(r'^search/(?P<country>[a-z]{2})$', views.PublishedDocumentSearchView.as_view(), name='public-search'),
]
