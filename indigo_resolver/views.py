from random import shuffle

from django.shortcuts import render
from django.http import HttpResponseBadRequest
from django.conf import settings

from cobalt.uri import FrbrUri

from indigo_api.models import Country
from .models import AuthorityReference


def resolve(request, frbr_uri):
    try:
        FrbrUri.default_language = None
        frbr_uri = FrbrUri.parse(frbr_uri)
    except ValueError:
        return HttpResponseBadRequest("Invalid FRBR URI")

    # language?
    if not frbr_uri.language:
        try:
            country = Country.for_code(frbr_uri.country)
            frbr_uri.language = country.primary_language.code
        except Country.DoesNotExist:
            frbr_uri.language = 'eng'

    # TODO: handle expression URIs and dates?
    references = list(
        AuthorityReference.objects
        .filter(frbr_uri__in=[frbr_uri.work_uri(), frbr_uri.expression_uri()])
        .prefetch_related('authority')
        .all())
    shuffle(references)

    return render(request, 'resolve.html', {
        'query': {
            'frbr_uri': frbr_uri,
            # TODO: more generic
            'title': "%s %s of %s" % (frbr_uri.doctype.title(), frbr_uri.number, frbr_uri.date),
            'type': frbr_uri.subtype or frbr_uri.doctype,
        },
        'references': references,
        'settings': settings,
    })
