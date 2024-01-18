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

        # Extract the messages
        messages = [
            {"message": message.message, "tags": message.tags}
            for message in get_messages(request)
        ]
        if not messages:
            return response

        # Get the existing HX-Trigger that could have been defined by the view
        hx_trigger = response.headers.get("HX-Trigger")

        if hx_trigger is None:
            # If the HX-Trigger is not set, start with an empty object
            hx_trigger = {}
        elif hx_trigger.startswith("{"):
            # If the HX-Trigger uses the object syntax, parse the object
            hx_trigger = json.loads(hx_trigger)
        else:
            # If the HX-Trigger uses the string syntax, convert to the object syntax
            hx_trigger = {hx_trigger: True}

        # Add the messages array in the HX-Trigger object
        hx_trigger["hx-messages"] = messages

        # Add or update the HX-Trigger
        response.headers["HX-Trigger"] = json.dumps(hx_trigger)

        return response
