from rest_framework.routers import DefaultRouter

from indigo_content_api.v2.router import router_patterns as router_patterns_v2
from indigo_content_api.v3.views import TaxonomyTopicWorkExpressionsView, WorkExpressionsViewSet, PlaceViewSet, \
    PlaceWorkExpressionsView


router_patterns = router_patterns_v2 + [
    # places will replace countries in the future
    (r'places', PlaceViewSet, 'place'),
    (r'places/(?P<frbr_uri_code>[^/.]+)/work-expressions', PlaceWorkExpressionsView, 'places-work-expressions'),
    (r'taxonomy-topics/(?P<slug>[^/.]+)/work-expressions', TaxonomyTopicWorkExpressionsView, 'taxonomy_topic-work-expressions'),
    ('work-expressions', WorkExpressionsViewSet, 'work_expression'),
]


def get_router():
    router = DefaultRouter(trailing_slash=False)
    for prefix, view, basename in router_patterns:
        router.register(prefix, view, basename=basename)
    return router
