from django.conf.urls import patterns, url, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'documents', views.DocumentViewSet)

urlpatterns = patterns('',
    url(r'^render', views.RenderAPI.as_view(), name='render'),
    url(r'^', include(router.urls)),
)
