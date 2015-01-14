from django.conf.urls import patterns, url, include
from rest_framework import routers

from indigo_dms import views

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'documents', views.DocumentViewSet)

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),

    url(r'^app/document/(?P<doc_id>\d+)/$', views.document, name='document'),

    url(r'^api/render', views.RenderAPI.as_view(), name='render'),
    url(r'^api/', include(router.urls)),
)
