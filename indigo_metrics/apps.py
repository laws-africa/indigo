from django.apps import AppConfig


class IndigoMetricsAppConfig(AppConfig):
    name = 'indigo_metrics'
    verbose_name = 'Indigo Metrics'

    def ready(self):
        import indigo_metrics.signals  # noqa
