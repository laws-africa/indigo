from django.conf.urls import patterns, url, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'documents', views.DocumentViewSet)

urlpatterns = patterns('',
    # viewing a specific document identified by FRBR URI fragment,
    # this requires at least 4 components in the FRBR URI,
    # starting with the two-letter country code
    #
    # eg. /za/act/2007/98
    url(r'^(?P<frbr_uri>[a-z]{2}[-/].*)$',
        views.PublishedDocumentDetailView.as_view({'get': 'get'}),
        name='published-document-detail'),

    url(r'^convert(\.(?P<format>[a-z0-9]))?$', views.ConvertView.as_view(), name='convert'),

    url(r'^', include(router.urls)),
)
