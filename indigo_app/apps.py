from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class IndigoAppConfig(AppConfig):
    name = 'indigo_app'
    verbose_name = 'Indigo Editor'


# Ensure that these translations are included by makemessages
_('Chapter')
_('Act')
_('Government Notice')
_('By-law')
