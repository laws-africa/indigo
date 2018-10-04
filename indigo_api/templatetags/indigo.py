from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def work_resolver_url(context, work):
    return context.get('resolver_url', settings.RESOLVER_URL) + work.frbr_uri
