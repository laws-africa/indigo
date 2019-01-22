from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

import views

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', views.CountryViewSet, base_name='country')

# Versioned API URLs
urlpatterns = [
    url(r'^v1/', include('indigo_content_api.urls_v1', namespace='v1'))
]
