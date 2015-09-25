from django.conf.urls import patterns, url, include
from django.views.generic.base import RedirectView

from . import views

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='library', permanent=True)),

    url(r'^documents/(?P<doc_id>\d+)/$', views.document, name='document'),
    url(r'^documents/new/$', views.document, name='new_document'),
    url(r'^documents/import/$', views.import_document, name='import_document'),
    url(r'^library/$', views.library, name='library'),

    url(r'^auth/', include('rest_auth.urls')),
    url(r'^auth/password/reset-confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.password_reset_confirm, name='password_reset_confirm'),
)
