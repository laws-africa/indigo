from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

import views

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', views.CountryViewSet, base_name='country')

urlpatterns = [
    url(r'^', include(router.urls)),

    # --- public content API ---
    # viewing a specific document identified by FRBR URI fragment,
    # this requires at least 4 components in the FRBR URI,
    # starting with the two-letter country code
    #
    # eg. /za/act/2007/98
    url(r'^akn/(?P<frbr_uri>[a-z]{2}[-/].*)$', views.PublishedDocumentDetailViewV2.as_view({'get': 'get'}), name='published-document-detail'),
    url(r'^search/(?P<country>[a-z]{2})$', views.PublishedDocumentSearchView.as_view(), name='public-search'),
]
