import itertools

registry = {}
_inf = float("-inf")


def register(cls):
    registry[cls.__name__] = cls


class RefRegistry(type):
    def __new__(cls, name, *args):
        newclass = super(RefRegistry, cls).__new__(cls, name, *args)
        if name != 'BaseRefFinder':
            register(newclass)
        return newclass


class RefFinders(object):
    """ Factory help class to find ref finders for a document.
    """
    @classmethod
    def for_document(cls, document):
        """ Find an appropriate finder for this document.
        """
        return cls.for_locale(country=document.country, locality=document.locality, language=document.language)

    @classmethod
    def for_locale(cls, country=None, language=None, locality=None):
        """ Find an appropriate finder for this locale description. Tightest match wins.
        """
        target = (country, language, locality)

        matches = ((finder, finder.locale_match(target)) for finder in registry.itervalues())
        matches = [(f, m) for f, m in matches if m]
        matches.sort()

        return matches[0][0]() if matches else None


class BaseRefFinder(object):
    """ Finds references to Acts in documents.

    Subclasses must implement `find_references_in_document`.
    """

    __metaclass__ = RefRegistry

    locale = (None, None, None)
    """ Locale for this finder, as a tuple: (country, language, locality). None matches anything. """

    def find_references_in_document(self, document):
        raise NotImplementedError()

    @classmethod
    def locale_match(cls, target):
        # compare target and locale tuples pair-wise, eliminate clashes
        # and score matches
        m = []

        for tgt, us in itertools.izip(target, cls.locale):
            if us is None:
                # we match anything
                m.append(_inf)
            elif tgt == us:
                # match
                m.append(True)
            else:
                # no match
                return None

        return tuple(m)
