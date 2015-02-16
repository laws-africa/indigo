from django.conf.urls import patterns, url, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'documents', views.DocumentViewSet)

urlpatterns = patterns('',
    url(r'^render', views.RenderAPI.as_view(), name='render'),

    # viewing a specific document identified by FRBR URI fragment,
    # this requires at least 4 components in the FRBR URI,
    # starting with the two-letter country code
    #
    # eg. /za/act/2007/98
    url(r'^(?P<frbr_uri>[a-z]{2}/[^/]+/[^/]+/[^/]+(.*))$',
        views.PublishedDocumentDetailView.as_view({'get': 'retrieve'}),
        name='published-document-detail'),

    # browsing documents by FRBR URI fragments, less than four,
    url(r'^(?P<frbr_uri>[a-z]{2}/.*/?)$',
        views.PublishedDocumentListView.as_view({'get': 'list'}),
        name='published-document-list'),

    url(r'^', include(router.urls)),
)
