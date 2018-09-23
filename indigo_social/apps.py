# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class IndigoSocialConfig(AppConfig):
    name = 'indigo_social'

    def ready(self):
        import indigo_social.badges  # noqa
