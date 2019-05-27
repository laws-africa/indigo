from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def work_resolver_url(context, work):
    if not work:
        return None

    if not isinstance(work, basestring):
        frbr_uri = work.frbr_uri
    else:
        frbr_uri = work
    return context.get('resolver_url', settings.RESOLVER_URL) + frbr_uri
