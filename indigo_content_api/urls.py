from django.conf.urls import url

import views


urlpatterns = [
    # --- public content API ---
    # viewing a specific document identified by FRBR URI fragment,
    # this requires at least 4 components in the FRBR URI,
    # starting with the two-letter country code
    #
    # eg. /za/act/2007/98
    url(r'^(?P<frbr_uri>[a-z]{2}[-/].*)$', views.PublishedDocumentDetailView.as_view({'get': 'get'}), name='published-document-detail'),
    url(r'^search/(?P<country>[a-z]{2})$', views.PublishedDocumentSearchView.as_view(), name='public-search'),
]
