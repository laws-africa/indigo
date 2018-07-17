from django import template
from django.conf import settings

register = template.Library()


@register.filter
def work_resolver_uri(work):
    return settings.RESOLVER_URL + work.frbr_uri
