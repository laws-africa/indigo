from django.apps import AppConfig


class IndigoContentAPIConfig(AppConfig):
    name = 'indigo_content_api'
    verbose_name = 'Indigo Content API'

    def ready(self):
        # intercept calls to reverse to use django_host's reverse
        from indigo_content_api.reverse import intercept_drf_reverse
        intercept_drf_reverse()
