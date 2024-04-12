from django.urls import include, path, re_path

from indigo_content_api.v2.urls_api import urlpatterns_base, router
from indigo_content_api.v3.views import PublishedDocumentDetailViewV3, TaxonomyTopicPublishedDocumentsView, \
    WorkExpressionsViewSet

router.register(r'taxonomy-topics/(?P<slug>[^/.]+)/work-expressions', TaxonomyTopicPublishedDocumentsView, basename='taxonomy_topic-work-expressions')
router.register('work-expressions', WorkExpressionsViewSet, basename='work_expression')

urlpatterns = urlpatterns_base + [
    path('', include(router.urls)),
    # eg. /akn/za/act/2007/98
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)$', PublishedDocumentDetailViewV3.as_view({'get': 'get'}), name='published-document-detail'),
]
