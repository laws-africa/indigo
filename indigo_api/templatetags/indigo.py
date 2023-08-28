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
def publication_document_description(work, placeholder=False, internal=False):
    """ Based on the information available, return a string describing the publication document for a work.
        If `placeholder` is True, return a minimum placeholder string.
        Otherwise, only return a string at all if at least one piece of publication information is available.
    """
    name = work.publication_name
    number = work.publication_number
    date = work.publication_date

    if date:
        if not internal:
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
def document_commencement_description(document):
    commencement_description = document.work.commencement_description_external()

    if commencement_description.subtype == 'multiple':
        # scope to document's date -- future commencements might not be applicable
        return document.work.commencement_description(
            scoped_date=document.expression_date,
            commencements=document.commencements_relevant_at_expression_date())

    return commencement_description
