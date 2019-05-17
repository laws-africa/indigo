from django.apps import AppConfig


class IndigoAppConfig(AppConfig):
    name = 'indigo_app'
    verbose_name = 'Indigo Editor'

    def ready(self):
        import indigo_app.notifications
