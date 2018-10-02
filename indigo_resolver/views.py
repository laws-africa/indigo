from random import shuffle

from django.http import HttpResponseBadRequest
from django.conf import settings
from django.views.generic import TemplateView

from cobalt.uri import FrbrUri

from indigo_api.models import Country
from .models import AuthorityReference


class ResolveView(TemplateView):
    template_name = 'resolve.html'

    def get(self, request, frbr_uri, **kwargs):
        try:
            FrbrUri.default_language = None
            self.frbr_uri = FrbrUri.parse(frbr_uri)
        except ValueError:
            return HttpResponseBadRequest("Invalid FRBR URI")

        # language?
        if not self.frbr_uri.language:
            try:
                country = Country.for_code(self.frbr_uri.country)
                self.frbr_uri.language = country.primary_language.code
            except Country.DoesNotExist:
                self.frbr_uri.language = 'eng'

        return super(ResolveView, self).get(self, frbr_uri=frbr_uri, **kwargs)

    def get_context_data(self, **kwargs):
        # TODO: handle expression URIs and dates?
        references = list(
            AuthorityReference.objects
            .filter(frbr_uri__in=[self.frbr_uri.work_uri(), self.frbr_uri.expression_uri()])
            .prefetch_related('authority')
            .all())
        shuffle(references)

        kwargs['query'] = {
            'frbr_uri': self.frbr_uri,
            # TODO: more generic
            'title': "%s %s of %s" % (self.frbr_uri.doctype.title(), self.frbr_uri.number, self.frbr_uri.date),
            'type': self.frbr_uri.subtype or self.frbr_uri.doctype,
        }
        kwargs['references'] = references
        kwargs['settings'] = settings

        return kwargs
