import logging

from django.conf import settings
import requests


log = logging.getLogger(__name__)


def send_slack_message(message, url=None, **kwargs):
    url = url or settings.SLACK_WEBHOOK_URL

    payload = {}
    payload.update(kwargs)
    if message:
        payload['text'] = message

    log.debug("Sending message to slack at %s: %s" % (url, payload))
    import json
    print json.dumps(payload)

    if not url:
        return

    timeout = getattr(settings, 'SLACK_TIMEOUT_SECS', 5)
    try:
        requests.post(url, json=payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        log.error("Error with slack call: %s" % e, exc_info=True)
