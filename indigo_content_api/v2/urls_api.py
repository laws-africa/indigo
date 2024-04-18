from django.urls import include, path, re_path

from . import views
from .router import get_router

urlpatterns_base = [
    # Work publication document
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media/publication/(?P<filename>.*)$', views.PublishedDocumentMediaView.as_view({'get': 'get_publication_document'}), name='published-document-publication'),
    # Get a specific media file
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media/(?P<filename>.*)$', views.PublishedDocumentMediaView.as_view({'get': 'get_file'}), name='published-document-file'),
]

urlpatterns_extra = [
    # eg. /akn/za/act/2007/98
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)$', views.PublishedDocumentDetailView.as_view({'get': 'get'}), name='published-document-detail'),
]

urlpatterns = urlpatterns_base + urlpatterns_extra + [
    path('', include(get_router().urls)),
]
