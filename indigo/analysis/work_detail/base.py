from __future__ import absolute_import

from django.utils.translation import ugettext as _

from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Subtype


@plugins.register('work-detail')
class BaseWorkDetail(LocaleBasedMatcher):
    """ Provides some locale-specific work details.

    Subclasses should implement `work_numbered_title`.
    """

    def work_numbered_title(self, work):
        """ Return a formatted title using the number for this work, such as "Act 5 of 2009".
        This usually differs from the short title. May return None.
        """
        uri = work.work_uri
        number = work.number
        work_type = self.work_friendly_type(work)

        # Should be in a locale-specific place
        if uri.number.startswith('cap'):
            # eg. Chapter 2
            number = number[3:]
            return _('%(type)s %(number)s') % {'type': _(work_type), 'number': number}

        return _('%(type)s %(number)s of %(year)s') % {'type': _(work_type), 'number': number, 'year': work.year}

    def work_friendly_type(self, work):
        """ Return a friendly document type for this work, such as "Act" or "By-law".
        """
        uri = work.work_uri

        # TODO: Should be in a locale-specific place
        if uri.number.startswith('cap'):
            # eg. Chapter 2
            return _('Chapter')

        elif uri.subtype:
            # use the subtype full name, if we have it
            subtype = Subtype.objects.filter(abbreviation=uri.subtype).first()
            if subtype:
                return _(subtype.name)
            return _(uri.subtype.upper())

        return _('Act')
