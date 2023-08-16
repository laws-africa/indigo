from copy import deepcopy

from django import template
from django.conf import settings
from django.utils.formats import date_format
from django.utils.translation import ugettext as _

from indigo.plugins import plugins

register = template.Library()


@register.simple_tag(takes_context=True)
def work_resolver_url(context, work):
    if not work:
        return None

    if not isinstance(work, str):
        frbr_uri = work.frbr_uri
    else:
        frbr_uri = work

    if context.get('media_resolver_use_akn_prefix') and not frbr_uri.startswith('/akn'):
        # for V2 APIs, prefix FRBR URI with /akn
        frbr_uri = '/akn' + frbr_uri

    return context.get('resolver_url', settings.RESOLVER_URL) + frbr_uri


@register.simple_tag
def commenced_provisions_description(document, commencement, uncommenced=False):
    # To get the provisions relevant to each row of the table,
    # use the earlier of the document's expression date and the relevant commencement's date
    date = document.expression_date
    # commencements can be dateless
    if commencement and commencement.date and date > commencement.date:
        date = commencement.date

    provisions = deepcopy(document.work.all_commenceable_provisions(date))
    provision_ids = document.work.all_uncommenced_provision_ids(document.expression_date) if uncommenced else commencement.provisions
    beautifier = plugins.for_document('commencements-beautifier', document)
    beautifier.commenced = not uncommenced

    return beautifier.make_beautiful(provisions, provision_ids)


@register.simple_tag
def has_uncommenced_provisions(document):
    return bool(document.work.all_uncommenced_provision_ids(document.expression_date))


@register.simple_tag
def publication_document_description(work, placeholder=False):
    """ Based on the information available, return a string describing the publication document for a work.
        If `placeholder` is True, return a minimum placeholder string.
        Otherwise, only return a string at all if at least one piece of publication information is available.
    """
    name = work.publication_name
    number = work.publication_number
    date = work.publication_date

    if date:
        date = date_format(date, 'j E Y')

        if name and number:
            # Published in Government Gazette 12345 on 1 January 2009
            return _('Published in %(name)s %(number)s on %(date)s') % {
                'name': name, 'number': number, 'date': date
            }
        elif name or number:
            # Published in Government Gazette on 1 January 2009; or
            # Published in 12345 on 1 January 2009
            return _('Published in %(name)s on %(date)s') % {
                'name': name or number, 'date': date
            }
        else:
            # Published on 1 January 2009
            return _('Published on %(date)s') % {
                'date': date
            }
    elif name and number:
        # Published in Government Gazette 12345
        return _('Published in %(name)s %(number)s') % {
            'name': name, 'number': number
        }
    elif name or number:
        # Published in Government Gazette; or
        # Published in 12345
        return _('Published in %(name)s') % {
            'name': name or number
        }
    elif placeholder:
        return _('Published')


@register.simple_tag
def work_commencement_description(work, friendly_date=True):
    """ Describes the commencement status of a work.
        Returns a tuple containing: (code, descriptive string, [optional commencing work tuple])
        Commencing work tuple contains:
            (commencing work object, title (which is either the numbered or short title), note with 'Note: ' prepended)

        Code: 0 = Uncommenced
              1 = Single commencement (full / partial; with/out date; with/out commencing work)
              2 = Multiple commencements

        Only code 1 works get a full description.
    """
    n_commencements = work.commencements.all().count()

    if n_commencements > 1:
        return 2, _('There are multiple commencements')

    if n_commencements == 0:
        return 0, _('Not commenced')

    else:
        # one commencement; may be in full or not, with/out a date, with/out a commencing work
        # (it may also be main or not, but we'll ignore that distinction when there's only one)
        # get and use the one commencement on the work -- don't assume that it's a main commencement --
        #   so don't use work.commencing_work or any of that, as those all rely on the main commencement
        commencement = work.commencements.first()

        # in full or not
        fully_commenced = commencement.all_provisions

        # with/out a commencing work
        commencing_work_description = None
        if commencement.commencing_work:
            # generate the tuple describing the commencing work
            commencing_title = commencement.commencing_work.numbered_title() or commencement.commencing_work.title
            commencement_note = commencement.note
            if commencement_note:
                commencement_note = _('Note: %(commencement_note)s') % {'commencement_note': commencement_note}
            commencing_work_description = (commencement.commencing_work, commencing_title, commencement_note)

        # with/out a date
        commencement_date = commencement.date

        if commencement_date:
            # format the date (in most cases)
            if friendly_date:
                commencement_date = date_format(commencement_date, 'j E Y')

            # with a date and a commencing work
            if commencing_work_description:
                if fully_commenced:
                    return 1, _('Commenced in full on %(date)s by') % {'date': commencement_date}, commencing_work_description
                return 1, _('Commenced in part on %(date)s by') % {'date': commencement_date}, commencing_work_description

            # with a date, without a commencing work
            if fully_commenced:
                return 1, _('Commenced in full on %(date)s') % {'date': commencement_date}
            return 1, _('Commenced in part on %(date)s') % {'date': commencement_date}

        # without a date, with a commencing work
        if commencing_work_description:
            if fully_commenced:
                return 1, _('Commenced in full by'), commencing_work_description
            return 1, _('Commenced in part by'), commencing_work_description

        # without a date or a commencing work
        if fully_commenced:
            return 1, _('Commenced in full')
        return 1, _('Commenced in part')
