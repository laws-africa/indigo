from django.conf.urls import patterns, url

from indigo_dms import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
)
