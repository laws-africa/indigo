from django.http import HttpResponseBadRequest
from django.conf import settings
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect

from cobalt.uri import FrbrUri

from indigo_api.models import Country
from .models import AuthorityReference, Authority


class ResolveView(TemplateView):
    template_name = 'resolve.html'

    def get_references(self):
        return [self.authority.lookup(self.frbr_uri)]

        # TODO: handle expression URIs and dates?
        query = AuthorityReference.objects\
            .filter(frbr_uri__in=[self.frbr_uri.work_uri(), self.frbr_uri.expression_uri()])\
            .prefetch_related('authority')

        if self.authority:
            query = query.filter(authority=self.authority)

        return query.all()

    def get_authority(self, authority):
        from .saflii import SafliiAuthority
        return SafliiAuthority()
        return get_object_or_404(Authority, name=authority) if authority else None

    def get(self, request, frbr_uri, authority, **kwargs):
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

        self.authority = self.get_authority(authority)
        self.references = self.get_references()

        # redirect if there's only one match
        if len(self.references) == 1:
            return redirect(self.references[0].url)

        return super(ResolveView, self).get(self, frbr_uri=frbr_uri, authority=authority, **kwargs)

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
