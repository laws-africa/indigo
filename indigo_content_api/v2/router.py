from rest_framework.routers import DefaultRouter

from . import views

# declaring the patterns and providing a get_router method rather than just creating a router
# directly in urls_api.py allows for the patterns to be reused in other routers and
# adjusted


router_patterns = [
    (r'countries', views.CountryViewSet, 'country'),
    (r'taxonomy-topics', views.TaxonomyTopicView, 'taxonomy_topic'),
    (r'(?P<frbr_uri>akn/[a-z]{2}[-/].*)/toc', views.PublishedDocumentTOCView, 'published-document-toc'),
    (r'(?P<frbr_uri>akn/[a-z]{2}[-/].*)/commencements', views.PublishedDocumentCommencementsView, 'published-document-commencements'),
    (r'(?P<frbr_uri>akn/[a-z]{2}[-/].*)/timeline', views.PublishedDocumentTimelineView, 'published-document-timeline'),
    (r'(?P<frbr_uri>akn/[a-z]{2}[-/]\S+?)/media', views.PublishedDocumentMediaView, 'published-document-media'),
]


def get_router():
    router = DefaultRouter(trailing_slash=False)
    for prefix, view, basename in router_patterns:
        router.register(prefix, view, basename=basename)
    return router
