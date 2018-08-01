from django.apps import AppConfig


class IndigoPLAppConfig(AppConfig):
    name = 'indigo_pl'
    verbose_name = 'Indigo Poland'

    def ready(self):
        # ensure our plugins are pulled in
        import indigo_pl.importer  # noqa
        import indigo_pl.toc  # noqa
