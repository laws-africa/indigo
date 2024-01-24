import re

from django.utils.translation import ugettext as _

from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Subtype


@plugins.register('work-detail')
class BaseWorkDetail(LocaleBasedMatcher):
    """ Provides some locale-specific work details.

    Subclasses should implement `work_numbered_title`.
    """

    no_numbered_title_subtypes = []
    """ These subtypes don't have numbered titles. """
    no_numbered_title_numbers = ['constitution']
    """ These numbers don't have numbered titles. """
    number_must_be_digit_doctypes = ['act']
    """ These doctypes only have numbered titles if the number starts with a digit."""

    def work_numbered_title(self, work):
        """ Return a formatted title using the number for this work, such as "Act 5 of 2009".
        This usually differs from the short title. May return None.
        """
        # check chapter first
        if work.place.settings.uses_chapter and work.properties.get('cap'):
            # eg. Chapter 2
            return _('Chapter %(cap)s') % {'cap': work.properties['cap']}

        number = work.number
        doctype = work.work_uri.doctype
        subtype = work.work_uri.subtype
        starts_with_digit = bool(re.match(r'^\d', number))

        # these don't have numbered titles
        if not subtype and doctype in self.number_must_be_digit_doctypes and not starts_with_digit:
            return None

        # these don't have numbered titles
        # also check partials, e.g. 'constitution-amendment' shouldn't get one
        if any(partial in self.no_numbered_title_numbers for partial in number.split("-")):
            return None

        # these don't have numbered titles
        if subtype in self.no_numbered_title_subtypes:
            return None

        work_type = self.work_friendly_type(work)
        return _('%(type)s %(number)s of %(year)s') % {'type': _(work_type), 'number': number.upper(), 'year': work.year}

    def work_friendly_type(self, work):
        """ Return a friendly document type for this work, such as "Act" or "By-law".
        """
        uri = work.work_uri

        if uri.subtype:
            # use the subtype full name, if we have it
            subtype = Subtype.for_abbreviation(uri.subtype)
            if subtype:
                return _(subtype.name)
            return _(uri.subtype.upper())

        return _(uri.doctype.title())
