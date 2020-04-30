from django.urls import include, path
from django.conf import settings


APP_NAME = 'indigo_content_api'

if settings.INDIGO_CONTENT_API_VERSIONED:
    # Versioned API URLs
    urlpatterns = [
        path('v1/', include(('indigo_content_api.v1.urls', APP_NAME), namespace='v1')),
        path('v2/', include(('indigo_content_api.v2.urls', APP_NAME), namespace='v2')),
    ]
else:
    # Unversioned API URLs, latest only
    urlpatterns = [
        path('', include(('indigo_content_api.urls_v2', APP_NAME), namespace='v2'))
    ]
