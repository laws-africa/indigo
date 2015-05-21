from django import template

register = template.Library()


@register.filter
def friendly_document_type(document):
    if document.number.startswith('cap'):
        return 'Chapter'
    else:
        # TODO: return based on document subtype
        return 'Act'


@register.filter
def friendly_document_number(document):
    if document.number.startswith('cap'):
        return document.number[3:]
    return document.number
