import logging

from django.http import HttpResponse
from django.views.generic import View

from indigo_app.views.base import AbstractAuthedIndigoView


log = logging.getLogger('django.request')


class JSErrorView(AbstractAuthedIndigoView, View):
    http_method_names = ['post']
    authentication_required = True

    def post(self, request, *args, **kwargs):
        # ensure empty value for expected variables
        info = {k: request.POST.get(k, '') for k in ['message', 'url', 'filename', 'lineno', 'colno', 'stack']}

        # This will email the admins if the 'mail_admin' logging handler is enabled.
        log.error(f"""JS error: {info['message']}
URL: {info['url']}
File: {info['filename']} @ {info['lineno']}:{info['colno']}

{info['stack']}
""")
        return HttpResponse(status=200)
