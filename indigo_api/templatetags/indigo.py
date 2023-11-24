from copy import deepcopy

from django import template
from django.conf import settings

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
