import re

from django.utils.translation import gettext as _

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
    chapter_names_choices = (
        ("chapter", _("Chapter")),
    )
    """ Subclasses can give choices in the Work form which will be used in the numbered title. """

    def work_numbered_title(self, work):
        """ Return a formatted title using the number for this work, such as "Act 5 of 2009".
        This usually differs from the short title. May return None.
        """
        # check chapter first
        chapter_number = self.work_chapter_number(work)
        if chapter_number:
            return f'{self.chapter_number_name(chapter_number)} {chapter_number.number}'

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

    def chapter_number_name(self, chapter_number):
        return dict(self.chapter_names_choices).get(chapter_number.name, _("Chapter"))

    def work_chapter_number(self, work):
        """ Returns the latest or only related ChapterNumber object.
            If there are multiple, the latest is the (only) one with the latest validity_start_date.
        """
        if work.chapter_numbers.count() == 1:
            # there's only one -- easy peasy
            return work.chapter_numbers.first()
        # only consider those with a start date
        chapter_numbers = work.chapter_numbers.filter(validity_start_date__isnull=False)
        if chapter_numbers.count() == 1:
            # there's only one with a start date -- easy peasy
            return chapter_numbers.first()
        # max() will complain if there are none left
        if chapter_numbers.exists():
            latest_start_date = max(x.validity_start_date for x in chapter_numbers)
            latest = chapter_numbers.filter(validity_start_date=latest_start_date)
            if latest.count() == 1:
                # there's only one at the latest start date -- we have a winner!
                return latest.first()

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
