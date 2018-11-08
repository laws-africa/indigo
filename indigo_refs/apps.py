from django.apps import AppConfig


class IndigoRefsAppConfig(AppConfig):
    name = 'indigo_refs'
    verbose_name = 'Indigo Refs'

    def ready(self):
        # ensure our plugins are pulled in
        import indigo_refs.refs  # noqa
