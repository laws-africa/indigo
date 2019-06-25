# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from importlib import import_module

from django.apps import AppConfig
from django.conf import settings


class IndigoSocialConfig(AppConfig):
    name = 'indigo_social'

    def ready(self):
        self.setup_country_badges()

    def setup_country_badges(self):
        import indigo_social.badges  # noqa

        # import default set of badges, if any
        if settings.INDIGO_SOCIAL['badges']:
            import_module(settings.INDIGO_SOCIAL['badges'])

        # ensure country badges get created
        indigo_social.badges.create_country_badges()
