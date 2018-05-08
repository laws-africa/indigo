from __future__ import unicode_literals

from django.utils.safestring import mark_safe
from django import template

from sass_processor.processor import SassProcessor


register = template.Library()


@register.simple_tag
def inline_scss(path):
    """ Template tag that compiles a scss and then inlines it.
    """
    processor = SassProcessor()
    path = processor(path)
    with processor.storage.open(path) as f:
        return mark_safe(f.read())
