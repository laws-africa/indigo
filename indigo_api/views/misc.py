from django.http import HttpResponse

from rest_framework.permissions import IsAuthenticated


def ping(request):
    return HttpResponse("pong", content_type="text/plain")


DEFAULT_PERMS = (IsAuthenticated,)
