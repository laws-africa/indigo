# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.signals import request_started


class IndigoSocialConfig(AppConfig):
    name = 'indigo_social'

    def ready(self):
        self.setup_country_badges()

    def setup_country_badges(self):
        import indigo_social.badges  # noqa

        # Install a once-off signal handler to create country badges before the
        # first request comes through. This allows us to work around the fact
        # that during testing, ready() is called before the database migrations
        # are applied, so no db tables exist. There doesn't seem to be a better
        # way to get code to run when the app starts up and AFTER the db has
        # been set up.
        uid = "indigo-social-country-setup"

        def create_badges(sender, **kwargs):
            request_started.disconnect(create_badges, dispatch_uid=uid)
            indigo_social.badges.CountryBadge.create_all()

        request_started.connect(create_badges, dispatch_uid=uid, weak=False)
