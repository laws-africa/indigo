from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView

from taggit.models import Tag
from languages_plus.models import Language, CultureCode
from countries_plus.models import Country
from rest_framework.authtoken.models import Token

import indigo_api.views.misc

admin.site.site_header = 'Indigo Admin'


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('indigo_api.urls')),
    url(r'^resolver/', include('indigo_resolver.urls')),
    url(r'^', include('indigo_social.urls')),

    url(r'^', include('indigo_app.urls')),
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    url(r'^ping$', indigo_api.views.misc.ping),
]


# remove some things from the admin area
admin.site.unregister(Tag)
admin.site.unregister(Language)
admin.site.unregister(CultureCode)
admin.site.unregister(Country)
admin.site.unregister(Token)
