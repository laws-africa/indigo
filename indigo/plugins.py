import logging
import itertools
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

    def for_document(self, topic, document):
        """ Find an appropriate helper for this document.
        """
        return self.for_locale(topic, country=document.country, locality=document.locality, language=document.language.code)

    def for_work(self, topic, work):
        return self.for_locale(topic, country=work.country, locality=work.locality, language=None)

    def for_locale(self, topic, country=None, language=None, locality=None):
        """ Find an appropriate importer for this locale description. Tightest match wins.
        """
        target = (country, language, locality)
        match = self.lookup(topic, target, self.registry[topic].itervalues())
        if match:
            # return an instance
            return match()

    def lookup(self, topic, target, candidates):
        matches = ((cls, cls.locale_match(target)) for cls in candidates)
        matches = ((f, m) for f, m in matches if m)
        matches = [(i, score) for i, score in matches if score]

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


class LocaleBasedMatcher(object):
    """ Mixin to support locale-based lookup.
    """

    locale = (None, None, None)
    """ Locale for this object, as a tuple: (country, language, locality). None matches anything."""

    @classmethod
    def locale_match(cls, target):
        """ Return a tuple ranking the match of `target` to this object.
        """
        m = []

        for tgt, us in itertools.izip(target, cls.locale):
            if us is None:
                # we match anything
                m.append(_inf)
            elif tgt == us:
                # match
                m.append(1)
            else:
                # no match
                return None

        return tuple(m)


class PluginRegistry(LocaleBasedRegistry):
    registry = defaultdict(dict)


plugins = PluginRegistry()
