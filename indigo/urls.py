from django.urls import include, path
from django.contrib import admin
from django.views.generic import TemplateView

from taggit.models import Tag
from languages_plus.models import Language, CultureCode
from countries_plus.models import Country
from rest_framework.authtoken.models import Token

import indigo_api.views.misc

admin.site.site_header = 'Indigo Admin'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('indigo_content_api.urls')),
    path('api/', include('indigo_api.urls')),
    path('resolver/', include('indigo_resolver.urls')),
    path('', include('indigo_social.urls')),
    path('', include('indigo_app.urls')),

    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('ping', indigo_api.views.misc.ping),
]


# remove some things from the admin area
admin.site.unregister(Tag)
admin.site.unregister(Language)
admin.site.unregister(CultureCode)
admin.site.unregister(Country)
admin.site.unregister(Token)
