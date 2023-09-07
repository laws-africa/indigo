from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from indigo_content_api.v2.urls import urlpatterns_base
from indigo_content_api.v2.views import CountryViewSet, TaxonomyTopicView
from indigo_content_api.v3.views import PublishedDocumentDetailViewV3

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', CountryViewSet, basename='country')
router.register(r'taxonomy_topics', TaxonomyTopicView, basename='taxonomy_topic')


urlpatterns = urlpatterns_base + [
    path(r'', include(router.urls)),
    # eg. /akn/za/act/2007/98
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)$', PublishedDocumentDetailViewV3.as_view({'get': 'get'}), name='published-document-detail'),
]
