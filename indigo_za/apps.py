from django.apps import AppConfig


class IndigoZAAppConfig(AppConfig):
    name = 'indigo_za'
    verbose_name = 'Indigo South Africa'

    def ready(self):
        # ensure our plugins are pulled in
        import indigo_za.terms  # noqa
        import indigo_za.work_detail  # noqa
