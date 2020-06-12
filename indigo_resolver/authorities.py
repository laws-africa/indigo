from django.conf import settings
from django.urls import reverse

from indigo_content_api.v2.views import PublishedDocumentDetailView
from indigo_resolver.models import Authority


class BaseAuthority(object):
    not_found_url = None

    def get_references(self, frbr_uri):
        raise NotImplementedError()


class Authorities(object):
    registry = {}

    def get(self, name):
        authority = self.registry.get(name)
        if authority:
            return authority

        return Authority.objects.filter(slug=name).first()

    def all(self):
        return list(self.registry.values()) + list(Authority.objects.all())

    def register(self, name=None):
        """ Class decorator that registers a new class with the registry.
        """
        def wrapper(cls):
            self.registry[name or cls.__name__] = cls()
            return cls
        return wrapper


authorities = Authorities()


class AuthorityReference:
    url = None
    frbr_uri = None
    title = None
    authority = None

    def __init__(self, url, frbr_uri, title, authority):
        self.url = url
        self.frbr_uri = frbr_uri
        self.title = title
        self.authority = authority

    def authority_name(self):
        return self.authority.name


@authorities.register('local')
class InternalAuthority(BaseAuthority):
    """ Resolver authority that redirects to the local database.
    """
    queryset = PublishedDocumentDetailView.queryset
    name = settings.INDIGO_ORGANISATION

    def get_references(self, frbr_uri):
        try:
            document = self.queryset.get_for_frbr_uri(frbr_uri)
        except ValueError:
            return []
        return [self.make_reference(document)]

    def make_reference(self, document):
        return AuthorityReference(
            url=reverse('work', kwargs={'frbr_uri': document.frbr_uri}),
            frbr_uri=document.frbr_uri,
            title=document.title,
            authority=self)
