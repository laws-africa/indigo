from django.conf.urls import url, include
from django.conf import settings
from rest_framework.routers import DefaultRouter

import views

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', views.CountryViewSet, base_name='country')

if settings.INDIGO_CONTENT_API_VERSIONED:
    # Versioned API URLs
    urlpatterns = [
        url(r'^v1/', include('indigo_content_api.urls_v1', namespace='v1')),
        url(r'^v2/', include('indigo_content_api.urls_v2', namespace='v2')),
    ]
else:
    # Unversioned API URLs, latest only
    urlpatterns = [
        url(r'^', include('indigo_content_api.urls_v1', namespace='v1'))
    ]
