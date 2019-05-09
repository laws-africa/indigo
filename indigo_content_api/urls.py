from django.conf.urls import url, include
from django.conf import settings


if settings.INDIGO_CONTENT_API_VERSIONED:
    # Versioned API URLs
    urlpatterns = [
        url(r'^v1/', include('indigo_content_api.v1.urls', namespace='v1')),
        url(r'^v2/', include('indigo_content_api.v2.urls', namespace='v2')),
    ]
else:
    # Unversioned API URLs, latest only
    urlpatterns = [
        url(r'^', include('indigo_content_api.urls_v1', namespace='v1'))
    ]
