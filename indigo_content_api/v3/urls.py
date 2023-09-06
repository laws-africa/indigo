from django.urls import re_path

from indigo_content_api.v2.urls import urlpatterns_base
from indigo_content_api.v3.views import PublishedDocumentDetailViewV3


urlpatterns = urlpatterns_base + [
    # eg. /akn/za/act/2007/98
    re_path(r'^(?P<frbr_uri>akn/[a-z]{2}[-/].*)$', PublishedDocumentDetailViewV3.as_view({'get': 'get'}), name='published-document-detail'),
]
