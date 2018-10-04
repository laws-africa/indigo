from itertools import chain

from django.http import HttpResponseBadRequest, Http404
from django.conf import settings
from django.views.generic import TemplateView
from django.shortcuts import redirect

from cobalt.uri import FrbrUri

from indigo_api.models import Country
from .authorities import authorities as registry


class ResolveView(TemplateView):
    template_name = 'resolve.html'

    def get(self, request, frbr_uri, authorities, *args, **kwargs):
        try:
            FrbrUri.default_language = None
            self.frbr_uri = FrbrUri.parse(frbr_uri)
        except ValueError:
            return HttpResponseBadRequest("Invalid FRBR URI")

        if not self.frbr_uri.language:
            try:
                country = Country.for_code(self.frbr_uri.country)
                self.frbr_uri.language = country.primary_language.code
            except Country.DoesNotExist:
                self.frbr_uri.language = 'eng'

        self.authorities = self.get_authorities(authorities)
        self.references = self.get_references()

        # redirect if there's only one match,
        # or if the user provided an explicit list of authorities
        # to try
        if self.references and (len(self.references) == 1 or authorities):
            return redirect(self.references[0].url)

        return super(ResolveView, self).get(self, frbr_uri=frbr_uri, authorities=authorities, *args, **kwargs)

    def get_authorities(self, authorities):
        if authorities:
            authorities = (registry.get(a) for a in authorities.split(','))
            authorities = [a for a in authorities if a]
            if not authorities:
                raise Http404()
            return authorities

        return registry.all()

    def get_references(self):
        return list(chain(*(a.get_references(self.frbr_uri) for a in self.authorities)))

    def get_context_data(self, **kwargs):
        kwargs['query'] = {
            'frbr_uri': self.frbr_uri,
            # TODO: more generic
            'title': "%s %s of %s" % (self.frbr_uri.doctype.title(), self.frbr_uri.number, self.frbr_uri.date),
            'type': self.frbr_uri.subtype or self.frbr_uri.doctype,
        }
        kwargs['references'] = self.references
        kwargs['settings'] = settings

        return kwargs
