from copy import deepcopy

from django import template
from django.conf import settings
from django.utils.formats import date_format
from django.utils.translation import ugettext as _

from indigo.plugins import plugins
from indigo_api.timeline import describe_publication_event

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
    event = describe_publication_event(work, with_date=True, friendly_date=not internal, placeholder=placeholder)
    if event:
        return event.description


@register.simple_tag
def work_as_at_date(work):
    # TODO: update work.as_at_date() and get rid of this
    """ Return either:
        - the as-at date override on this work, or
        - the work's latest expression's date, or
        - the as-at date for the work's place, if it's after the work's latest expression, or
        - None
    """
    as_at_date = work.as_at_date_override
    if not as_at_date:
        expressions = work.expressions()
        as_at_date = max([d.expression_date for d in expressions]) if expressions else as_at_date
        place_date = work.place.settings.as_at_date

        # no latest expression -- fall back to the place's date (can be None)
        if not as_at_date:
            as_at_date = place_date

        # only use the place's date if it's later than the latest expression's
        elif place_date and place_date > as_at_date:
            as_at_date = place_date

    return as_at_date


@register.simple_tag
def document_commencement_description(document):
    commencement_description = document.work.commencement_description_external()

    if commencement_description.subtype == 'multiple':
        # scope to document's date -- future commencements might not be applicable
        commencements = document.commencements_relevant_at_expression_date()
        document_has_uncommenced_provisions = None
        # we only care about whether there are uncommenced provisions in the case of a single commencement
        # (it's not cheap to calculate)
        if len(commencements) == 1:
            document_has_uncommenced_provisions = has_uncommenced_provisions(document)
        return document.work.commencement_description(
            commencements=commencements,
            has_uncommenced_provisions=document_has_uncommenced_provisions)

    return commencement_description
