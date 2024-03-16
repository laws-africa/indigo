from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from indigo_content_api.v2.urls import urlpatterns_base
from indigo_content_api.v2.views import CountryViewSet, TaxonomyTopicView
from indigo_content_api.v3.views import PublishedDocumentDetailViewV3, TaxonomyTopicPublishedDocumentsView

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', CountryViewSet, basename='country')
router.register(r'taxonomy-topics', TaxonomyTopicView, basename='taxonomy_topic')


urlpatterns = urlpatterns_base + [
    path(r'', include(router.urls)),

    # eg. /akn/za/act/2007/98
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)$', PublishedDocumentDetailViewV3.as_view({'get': 'get'}), name='published-document-detail'),

    # taxonomy topic work list
    path('taxonomy-topics/<slug:slug>/work-expressions', TaxonomyTopicPublishedDocumentsView.as_view({'get': 'list'}), name='taxonomy_topic-work-expressions'),
    path('taxonomy-topics/<slug:slug>/work-expressions.<slug:format>', TaxonomyTopicPublishedDocumentsView.as_view({'get': 'list'}),
         name='taxonomy_topic-work-expressions'),
]
