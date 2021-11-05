from django.apps import AppConfig
from django.conf import settings


class IndigoApiConfig(AppConfig):
    name = 'indigo_api'
    verbose_name = 'Indigo API'

    def ready(self):
        from actstream import registry
        from django.contrib.auth.models import User
        from indigo_api.models import Amendment, Document, Task, Work, Workflow, PlaceSettings, ArbitraryExpressionDate, Commencement
        registry.register(Amendment)
        registry.register(Document)
        registry.register(Task)
        registry.register(User)
        registry.register(Work)
        registry.register(Workflow)
        registry.register(PlaceSettings)
        registry.register(ArbitraryExpressionDate)
        registry.register(Commencement)

        if not settings.DEBUG:
            from indigo_api.tasks import setup_pruning
            setup_pruning()
