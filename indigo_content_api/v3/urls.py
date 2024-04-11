from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from indigo_content_api.v2.urls import urlpatterns_base
from indigo_content_api.v2.views import CountryViewSet, TaxonomyTopicView
from indigo_content_api.v3.views import PublishedDocumentDetailViewV3, TaxonomyTopicPublishedDocumentsView, \
    WorkExpressionsViewSet

router = DefaultRouter(trailing_slash=False)
router.register('countries', CountryViewSet, basename='country')
router.register('taxonomy-topics', TaxonomyTopicView, basename='taxonomy_topic')
router.register(r'taxonomy-topics/(?P<slug>[^/.]+)/work-expressions', TaxonomyTopicPublishedDocumentsView, basename='taxonomy_topic-work-expressions')
router.register('work-expressions', WorkExpressionsViewSet, basename='work_expression')

urlpatterns = urlpatterns_base + [
    path('', include(router.urls)),
    # eg. /akn/za/act/2007/98
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)$', PublishedDocumentDetailViewV3.as_view({'get': 'get'}), name='published-document-detail'),

    path(
        "schema",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        "schema/swagger-ui",
        SpectacularSwaggerView.as_view(url_name="v3:schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc", SpectacularRedocView.as_view(url_name="v3:schema"), name="redoc"
    ),
]
