from django.apps import AppConfig


class IndigoAppConfig(AppConfig):
    name = 'indigo_app'
    verbose_name = 'Indigo Editor'

    def ready(self):
        from actstream import registry
        from indigo_api.models import Task
        registry.register(Task)
