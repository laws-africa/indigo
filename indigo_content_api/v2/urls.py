from django.urls import include, path
from django.conf import settings
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('', include(settings.INDIGO['CONTENT_API']['URLCONF']['v2'])),
    path(
        'schema',
        SpectacularAPIView.as_view(
            api_version='v2',
            urlconf=settings.INDIGO['CONTENT_API']['URLCONF']['v2'],
            custom_settings={
                'SCHEMA_PATH_PREFIX_INSERT': settings.INDIGO['CONTENT_API']['API_PREFIX'] + 'v2',
            }
        ),
        name='v2_schema',
    ),
    path('schema/swagger-ui', SpectacularSwaggerView.as_view(url_name='indigo_content_api:v2_schema')),
    path('schema/redoc', SpectacularRedocView.as_view(url_name='indigo_content_api:v2_schema')),
]
