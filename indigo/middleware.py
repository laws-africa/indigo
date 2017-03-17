from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from UniversalAnalytics import Tracker


class GoogleAnalyticsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if self.ignore(request):
            return response

        client_id = request.COOKIES.get('_ga')
        if client_id:
            # GA1.2.1760224793.1424413995
            client_id = client_id.split('.', 2)[-1]

        if 'HTTP_X_FORWARDED_FOR' in request.META:
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
        else:
            client_ip = request.META.get('REMOTE_ADDR', '')

        self.send(client_id, 'pageview', request.path,
                  userIp=client_ip,
                  referrer=request.META.get('HTTP_REFERER', ''),
                  userAgent=request.META.get('HTTP_USER_AGENT', ''))

        return response

    def send(self, client_id, *args, **kwargs):
        tracker = Tracker.create(settings.GOOGLE_ANALYTICS_ID, client_id=client_id)
        tracker.send(*args, **kwargs)

    def ignore(self, request):
        if hasattr(settings, 'GOOGLE_ANALYTICS_INCLUDE_PATH'):
            if not any(request.path.startswith(p) for p in settings.GOOGLE_ANALYTICS_INCLUDE_PATH):
                return True

        if hasattr(settings, 'GOOGLE_ANALYTICS_EXCLUDE_PATH'):
            if any(request.path.startswith(p) for p in settings.GOOGLE_ANALYTICS_EXCLUDE_PATH):
                return True

        if hasattr(settings, 'GOOGLE_ANALYTICS_IGNORE_USER_AGENT'):
            if settings.GOOGLE_ANALYTICS_IGNORE_USER_AGENTS.search(request.META.get('HTTP_USER_AGENT', '')):
                return True

        return False
