from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('', include('indigo_content_api.v3.urls_api')),
    path(
        "schema",
        SpectacularAPIView.as_view(
            api_version='v3',
            urlconf='indigo_content_api.v3.urls_api',
            custom_settings={
                "SCHEMA_PATH_PREFIX_INSERT": "api/v3",
            }
        ),
        name="v3_schema",
    ),
    path("schema/swagger-ui", SpectacularSwaggerView.as_view(url_name="indigo_content_api:v3_schema")),
    path("schema/redoc", SpectacularRedocView.as_view(url_name="indigo-content-api:v3_schema")),
]
