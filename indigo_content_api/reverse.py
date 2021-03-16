""" This module has helper routines to assist with reverse Content API URLs when the Content API
might be running on a separate domain using django_hosts. In such a case, the App still needs to
reverse certain API URLs and by default Django would try to use the App's URLs, not the API's URLs.
"""

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
    """
    if using_django_hosts():
        kwargs.setdefault('host', CONTENT_API_HOST)
    return drf_reverse(*args, **kwargs)


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
