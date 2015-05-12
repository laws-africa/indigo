from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.site.site_header = 'Indigo Admin'

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('indigo_api.urls')),

    url(r'^', include('indigo_app.urls')),
)
