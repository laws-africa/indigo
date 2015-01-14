from django.conf.urls import patterns, url, include

from . import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),

    url(r'^documents/(?P<doc_id>\d+)/$', views.document, name='document'),
)
