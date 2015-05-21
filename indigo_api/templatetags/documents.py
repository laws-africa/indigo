from django import template

from indigo_api.models import Subtype

register = template.Library()


@register.filter
def friendly_document_type(document):
    uri = document.doc.frbr_uri

    if uri.number.startswith('cap'):
        return 'Chapter'

    if uri.subtype:
        # use the subtype full name, if we have it
        subtype = Subtype.objects.filter(abbreviation=uri.subtype).first()
        if subtype:
            return subtype.name
        return uri.subtype.upper()

    return 'Act'


@register.filter
def friendly_document_number(document):
    if document.number.startswith('cap'):
        return document.number[3:]
    return document.number
