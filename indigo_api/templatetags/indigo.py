from django import template
from django.conf import settings

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
    language = document.language
    if uncommenced:
        uncommenced_provisions = document.work.uncommenced_provisions()
        return ', '.join([p.id for p in uncommenced_provisions])

    return ', '.join(commencement.provisions)
