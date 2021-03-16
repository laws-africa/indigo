import logging
from collections import defaultdict

log = logging.getLogger(__name__)
_inf = float("-inf")


class LocaleBasedRegistry(object):
    """ Base class for locale-based registries. Helps register and lookup locale-based classes.
    """

    registry = None
    """ Registry of class names to classes. Subclasses MUST define this to avoid
    sharing registry classes.
    """

    def for_document(self, topic, document, many=False):
        """ Find an appropriate helper for this document.
        """
        locality = document.work.locality.code if document.work.locality else None
        return self.for_locale(topic, country=document.work.country.code, locality=locality, language=document.language.code, many=many)

    def for_work(self, topic, work, many=False):
        """ Find an appropriate helper for this work.
        """
        locality = work.locality.code if work.locality else None
        return self.for_locale(topic, country=work.country.code, locality=locality, language=None, many=many)

    def for_locale(self, topic, country=None, language=None, locality=None, many=False):
        """ Find an appropriate importer for this locale description. Tightest match wins.
        """
        target = (country, language, locality)
        match = self.lookup(topic, target, self.registry[topic].values(), many=many)

        def create(m):
            return m() if type(m) == type else m

        if many:
            # return all instances
            return [create(m) for m in match]

        if match:
            # return an instance
            return create(match)

    def lookup(self, topic, target, candidates, many=False):
        matches = ((cls, cls.locale_match(target)) for cls in candidates)
        matches = ((f, m) for f, m in matches if m)
        matches = [(i, score) for i, score in matches if score]

        if many:
            return [m[0] for m in matches]

        # sort by score, best match last
        matches.sort(key=lambda x: x[1])
        log.debug("Looking for %s match for %s, candidates (best is last): %s" % (topic, target, matches))

        if matches:
            return matches[-1][0]

    def register(self, topic, name=None):
        """ Class decorator that registers a new class with the registry.
        """
        def wrapper(cls):
            self.registry[topic][name or cls.__name__] = cls
            return cls
        return wrapper

    def register_instance(self, topic, name, inst):
        """ Registers an object with the registry.
        """
        self.registry[topic][name] = inst


class LocaleBasedMatcher(object):
    """ Mixin to support locale-based lookup.
    """

    locale = (None, None, None)
    """ Locale for this object, as a tuple: (country, language, locality). None matches anything.
    Each entry can also be a list.
    """

    @classmethod
    def locale_match(cls, target):
        return plugins.locale_match(target, cls.locale)


class PluginRegistry(LocaleBasedRegistry):
    registry = defaultdict(dict)

    def locale_match(self, target, candidate):
        """ Return a tuple ranking the match of `target` to `candidate`. Each entry in the tuple is an integer
        score for the match against the corresponding entry in the `locale` tuple: country, language, locality.

        Bigger scores mean a better match. Returns None to indicate no match at all.
        """
        m = []

        for tgt, cand in zip(target, candidate):
            if cand is None:
                # we match anything
                m.append(_inf)
            elif tgt == cand or (isinstance(cand, list) and tgt in cand):
                # match
                m.append(1)
            else:
                # no match
                return None

        return tuple(m)


plugins = PluginRegistry()
