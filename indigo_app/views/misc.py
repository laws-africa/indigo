import logging

from django.http import HttpResponse
from django.views.generic import View

from indigo_app.views.base import AbstractAuthedIndigoView


log = logging.getLogger(__name__)


class JSErrorView(AbstractAuthedIndigoView, View):
    http_method_names = ['post']
    authentication_required = True

    def post(self, request, *args, **kwargs):
        info = request.POST.dict()
        # This will email the admins if the 'mail_admin' logging handler is enabled.
        log.error(f"JS error:\n\n{info['message']}\n\n{info['filename']} @ {info['lineno']}:{info['colno']}")
        return HttpResponse(status=200)
