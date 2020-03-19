import logging
import re

from django.http import HttpResponse
from django.views.generic import View

from indigo_app.views.base import AbstractAuthedIndigoView


log = logging.getLogger(__name__)
request_log = logging.getLogger('django.request')


class JSErrorView(AbstractAuthedIndigoView, View):
    http_method_names = ['post']
    authentication_required = True

    # ignore messages from these files
    filename_blacklist = [
        re.compile(r'/ckeditor/'),
    ]

    def post(self, request, *args, **kwargs):
        # ensure empty value for expected variables
        info = {k: request.POST.get(k, '') for k in ['message', 'url', 'filename', 'lineno', 'colno', 'stack']}

        if any(x.search(info['filename']) for x in self.filename_blacklist):
            log.info(f"Ignoring JS error: {info['message']} in {info['filename']}")
        else:
            # This will email the admins if the 'mail_admin' logging handler is enabled.
            request_log.error(f"""JS error: {info['message']}
    URL: {info['url']}
    File: {info['filename']} @ {info['lineno']}:{info['colno']}

    {info['stack']}
    """, extra={'request': request})

        return HttpResponse(status=200)
