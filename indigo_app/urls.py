from django.conf.urls import patterns, url, include
from django.views.generic.base import RedirectView

from . import views

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='library', permanent=True)),

    url(r'^documents/(?P<doc_id>\d+)/$', views.document, name='document'),
    url(r'^library/$', views.library, name='library'),
)
