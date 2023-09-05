from django.urls import include, path
from django.conf import settings


APP_NAME = 'indigo_content_api'

if settings.INDIGO_CONTENT_API_VERSIONED:
    # Versioned API URLs
    urlpatterns = [
        path('v2/', include(('indigo_content_api.v2.urls', APP_NAME), namespace='v2')),
        path('v3/', include(('indigo_content_api.v3.urls', APP_NAME), namespace='v3')),
    ]
else:
    # Unversioned API URLs, latest only
    urlpatterns = [
        # TODO: where is urls_v2 currently?
        path('', include(('indigo_content_api.urls_v2', APP_NAME), namespace='v3'))
    ]
