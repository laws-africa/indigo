from django.conf.urls import url

import indigo_resolver.views


urlpatterns = [
    # TODO: support json
    url(r'^resolve(?P<frbr_uri>/.*)$', indigo_resolver.views.resolve),
]
