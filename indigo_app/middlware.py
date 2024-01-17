from django.contrib.messages import get_messages
import json
from datetime import datetime, timedelta
from django.template.loader import render_to_string
class HtmxMessagesMiddleware:
    """ Adds a message to the Django messages framework if the request is an htmx request.
    """

    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        response = self.get_response(request)
        # The HX-Request header indicates that the request was made with HTMX
        if "HX-Request" not in request.headers:
            return response

        # Ignore redirections because HTMX cannot read the headers
        if 300 <= response.status_code < 400:
            return response

        # check for messages
        messages = get_messages(request)
        if not messages:
            return response

        response.write(
            render_to_string("_messages.html", {"messages": messages}, request=request)
        )
        return response
