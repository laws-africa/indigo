from django.http import HttpResponse
from django.conf import settings

from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly


def ping(request):
    return HttpResponse("pong", content_type="text/plain")


if settings.INDIGO_AUTH_REQUIRED:
    DEFAULT_PERMS = (IsAuthenticated,)
else:
    DEFAULT_PERMS = (IsAuthenticatedOrReadOnly,)
