from django import template

register = template.Library()


@register.filter
def publication_number(document):
    """ The publication number can be split with a - which indicates
    a number and a poz.
    """
    if document.publication_number and '-' in document.publication_number:
        return document.publication_number.split("-")[0]


@register.filter
def publication_poz(document):
    """ The publication number can be split with a - which indicates
    a number and a poz.
    """
    if document.publication_number and '-' in document.publication_number:
        return document.publication_number.split("-")[1]
    return document.publication_number
