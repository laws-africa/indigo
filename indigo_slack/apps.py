from django.apps import AppConfig


class IndigoSlackConfig(AppConfig):
    name = 'indigo_slack'
    verbose_name = 'Indigo Slack'

    def ready(self):
        # ensure signal handlers are installed
        import indigo_slack.notifications  # noqa
