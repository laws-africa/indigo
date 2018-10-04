from django.conf.urls import url

import indigo_resolver.views


urlpatterns = [
    url(r'^((?P<authorities>[\w,.-]+)/)?resolve(?P<frbr_uri>/.*)$', indigo_resolver.views.ResolveView.as_view(), name='resolver'),
]
