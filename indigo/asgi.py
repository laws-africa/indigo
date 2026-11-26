"""Shared HTTP-only ASGI application for Indigo deployments.

Downstream projects must set DJANGO_SETTINGS_MODULE before importing application.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "indigo.settings")

django_application = get_asgi_application()


async def application(scope, receive, send):
    # Reject unsupported upgrades before they reach Django's HTTP-only handler.
    if scope["type"] == "websocket":
        await send({"type": "websocket.close", "code": 1000})
        return

    await django_application(scope, receive, send)
