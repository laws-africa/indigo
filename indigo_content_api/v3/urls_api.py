from django.urls import include, path, re_path

from indigo_content_api.v2.urls_api import urlpatterns_base
from .router import get_router
from .views import PublishedDocumentDetailViewV3

urlpatterns_extra = [
    # eg. /akn/za/act/2007/98
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)$', PublishedDocumentDetailViewV3.as_view({'get': 'get'}), name='published-document-detail'),
]

urlpatterns = urlpatterns_base + [
    path('', include(get_router().urls)),
] + urlpatterns_extra
