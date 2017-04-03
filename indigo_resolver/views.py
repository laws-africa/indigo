from django.shortcuts import render
from django.http import HttpResponseBadRequest

from cobalt.uri import FrbrUri

from .models import AuthorityReference


def resolve(request, frbr_uri):
    try:
        frbr_uri = FrbrUri.parse(frbr_uri)
    except ValueError:
        return HttpResponseBadRequest("Invalid FRBR URI")

    # TODO: handle expression URIs and dates?
    references = AuthorityReference.objects\
        .filter(frbr_uri__in=[frbr_uri.work_uri(), frbr_uri.expression_uri()])\
        .prefetch_related('authority')\
        .all()

    return render(request, 'resolve.html', {
        'query': {
            'frbr_uri': frbr_uri,
            # TODO: more generic
            'title': "%s %s of %s" % (frbr_uri.doctype.title(), frbr_uri.number, frbr_uri.date),
            'type': frbr_uri.subtype or frbr_uri.doctype,
        },
        'references': references,
    })
