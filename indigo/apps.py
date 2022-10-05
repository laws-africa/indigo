import logging
import os

from django.apps import AppConfig
from django.conf import settings
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


class IndigoAppConfig(AppConfig):
    name = 'indigo'
    verbose_name = 'Indigo'

    def ready(self):
        # ensure our plugins are pulled in
        import indigo.analysis      # noqa
        import indigo.bulk_creator  # noqa

        # setup sentry error reporting
        if not settings.DEBUG and os.environ.get('SENTRY_DSN'):
            import indigo.signals       # noqa

            # sentry sentry
            sentry_logging = LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=None,  # Don't send errors based on log messages
            )

            sentry_sdk.init(
                dsn=os.environ.get('SENTRY_DSN'),
                integrations=[DjangoIntegration(), sentry_logging],
                send_default_pii=True,
                traces_sample_rate=0.5,  # sample 50% of requests for performance metrics
            )
