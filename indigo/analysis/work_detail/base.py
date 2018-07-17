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
        work_type = 'Act'

        # Should be in a locale-specific place
        if uri.number.startswith('cap'):
            # eg. Chapter 2
            work_type = 'Chapter'
            number = number[3:]
            return _('%(type)s %(number)s') % {'type': _(work_type), 'number': number}

        elif uri.subtype:
            # use the subtype full name, if we have it
            subtype = Subtype.objects.filter(abbreviation=uri.subtype).first()
            if subtype:
                work_type = subtype.name
            else:
                work_type = uri.subtype.upper()

        return _('%(type)s %(number)s of %(year)s') % {'type': _(work_type), 'number': number, 'year': work.year}
