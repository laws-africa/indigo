from django.apps import AppConfig


class IndigoApiConfig(AppConfig):
    name = 'indigo_api'
    verbose_name = 'Indigo API'

    def ready(self):
        from actstream import registry
        from django.contrib.auth.models import User
        from indigo_api.models import Amendment, Document, Task, Work, Workflow
        registry.register(Amendment)
        registry.register(Document)
        registry.register(Task)
        registry.register(User)
        registry.register(Work)
        registry.register(Workflow)
