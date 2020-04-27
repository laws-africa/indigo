from django.urls import re_path

import indigo_resolver.views


urlpatterns = [
    re_path(r'^((?P<authorities>[\w,.-]+)/)?resolve(?P<frbr_uri>/.*)$', indigo_resolver.views.ResolveView.as_view(), name='resolver'),
]
