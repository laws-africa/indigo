from indigo_content_api.v1.views import PublishedDocumentDetailView
from indigo_resolver.models import AuthorityReference, Authority


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
