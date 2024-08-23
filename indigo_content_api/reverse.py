""" This module has helper routines to assist with reverse Content API URLs when the Content API
might be running on a separate domain using django_hosts. In such a case, the App still needs to
reverse certain API URLs and by default Django would try to use the App's URLs, not the API's URLs.
"""

from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.urls import reverse as django_reverse
from rest_framework.reverse import reverse as drf_reverse

# the host alias that runs the content_api, if django_hosts is in use
CONTENT_API_HOST = 'api'


def using_django_hosts():
    return getattr(settings, 'ROOT_HOSTCONF', None)


def reverse_content_api(*args, **kwargs):
    """ Reverses an Indigo Content API url by delegating to the django_rest_framework reverse.

    If django_hosts is in use, then a host parameter is added so that the appropriate API urlconf is used.

    While the base Indigo doesn't enable django_hosts by default, this allows Indigo users to
    opt-in to django_hosts and host the API on a separate hostname.

    If django_rest_framework returns a non-absolute URL (e.g. because a request isn't given,
    and/or django_hosts is not in use), then use settings.INDIGO_URL to build the absolute URL.
    """
    if using_django_hosts():
        kwargs.setdefault('host', CONTENT_API_HOST)
    url = drf_reverse(*args, **kwargs)

    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        parsed_base_url = urlparse(settings.INDIGO_URL)
        # combine e.g. http://localhost:8000 with e.g. /api/v3/akn/…
        url = urlunparse((
            parsed_base_url.scheme, parsed_base_url.netloc,
            parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))

    return url


def intercept_drf_reverse():
    """ Intercept DRF's call to django_reverse to first try calling django_hosts's reverse.
    """
    if using_django_hosts():
        import rest_framework.reverse
        rest_framework.reverse.django_reverse = host_aware_reverse


def host_aware_reverse(*args, **kwargs):
    if 'host' in kwargs:
        from django_hosts import reverse as dh_reverse
        return dh_reverse(*args, **kwargs)

    return django_reverse(*args, **kwargs)
