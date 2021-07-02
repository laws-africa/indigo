from copy import deepcopy

from django import template
from django.conf import settings

from indigo.analysis.toc.base import CommencementsBeautifier

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
    if commencement and date > commencement.date:
        date = commencement.date

    provisions = deepcopy(document.work.all_commenceable_provisions(date))
    provision_ids = document.work.all_uncommenced_provision_ids(document.expression_date) if uncommenced else commencement.provisions

    beautifier = CommencementsBeautifier(commenced=not uncommenced)
    # decorate the ToC with useful information
    provisions = beautifier.decorate_provisions(provisions, provision_ids)
    return beautifier.make_beautiful(provisions)


@register.simple_tag
def commencements_relevant_at_date(document):
    return document.commencements_relevant_at_expression_date()

@register.simple_tag
def has_uncommenced_provisions(document):
    return bool(document.work.all_uncommenced_provision_ids(document.expression_date))
