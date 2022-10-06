from django.apps import AppConfig


class IndigoAppConfig(AppConfig):
    name = 'indigo'
    verbose_name = 'Indigo'

    def ready(self):
        # ensure our plugins are pulled in
        import indigo.analysis      # noqa
        import indigo.bulk_creator  # noqa
        import indigo.signals       # noqa
