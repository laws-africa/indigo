from indigo_api.views.public import PublishedDocumentDetailView
from indigo_resolver.models import AuthorityReference, Authority


class Authorities(object):
    registry = {}

    def get(self, name):
        authority = self.registry.get(name)
        if authority:
            return authority

        return Authority.objects.filter(slug=name).first()

    def all(self):
        return self.registry.values() + list(Authority.objects.all())

    def register(self, name=None):
        """ Class decorator that registers a new class with the registry.
        """
        def wrapper(cls):
            self.registry[name or cls.__name__] = cls()
            return cls
        return wrapper


authorities = Authorities()


@authorities.register('saflii.org')
class SafliiAuthority(object):
    queryset = PublishedDocumentDetailView.queryset
    name = 'SAFLII'

    def get_references(self, frbr_uri):
        try:
            document = self.queryset.get_for_frbr_uri(frbr_uri)
            return [self.make_reference(document)]
        except ValueError:
            return []

    def make_reference(self, document):
        url = self.get_external_url(document)
        return AuthorityReference(url=url, frbr_uri=document.frbr_uri, title=document.title, authority=self)

    def get_external_url(self, document):
        """ Mimic SAFLII's mechanism for determining unique URLs for a
        document, based on its title.

        Eg. "National Environmental Management: Air Quality Act (Act 39 of 2004)" -> "nemaqa39o2004494"
        """
        title = '%s (Act %s of %s)' % (document.title, document.number, document.year)
        title = title.lower()

        # gather up any digit, or the first alpha char after a space or at the start of the string
        parts = [
            str(c) for i, c in enumerate(title)
            if c.isdigit() or (title[i].isalpha() and (i == 0 or title[i - 1].isspace()))
        ]

        count = sum([ord(c) - ord('a') for c in title if c.isalpha()])
        fragment = ''.join(parts) + str(count)

        return 'http://www.saflii.org/za/legis/legislation/%s/' % fragment
