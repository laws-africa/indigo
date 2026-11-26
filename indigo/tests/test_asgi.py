from unittest.mock import AsyncMock, patch

from django.test import SimpleTestCase

from indigo.asgi import application


class ASGIApplicationTestCase(SimpleTestCase):
    async def test_rejects_websocket_handshakes_without_calling_django(self):
        for path in ("/websocket", "/socket.io/", "/api/"):
            with self.subTest(path=path):
                scope = {
                    "type": "websocket",
                    "path": path,
                    "headers": [(b"host", b"example.com")],
                }
                receive = AsyncMock(return_value={"type": "websocket.connect"})
                send = AsyncMock()

                with patch("indigo.asgi.django_application", new_callable=AsyncMock) as django_app:
                    await application(scope, receive, send)

                django_app.assert_not_awaited()
                send.assert_awaited_once_with({"type": "websocket.close", "code": 1000})

    async def test_passes_http_requests_to_django_unchanged(self):
        scope = {"type": "http", "path": "/api/", "method": "POST"}
        receive = AsyncMock()
        send = AsyncMock()

        with patch("indigo.asgi.django_application", new_callable=AsyncMock) as django_app:
            await application(scope, receive, send)

        django_app.assert_awaited_once_with(scope, receive, send)
        receive.assert_not_awaited()
        send.assert_not_awaited()

    async def test_does_not_suppress_http_errors(self):
        with patch("indigo.asgi.django_application", new_callable=AsyncMock) as django_app:
            django_app.side_effect = ValueError("HTTP handler error")

            with self.assertRaisesMessage(ValueError, "HTTP handler error"):
                await application({"type": "http"}, AsyncMock(), AsyncMock())
