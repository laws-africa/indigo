import itertools
from collections import defaultdict

registry = defaultdict(dict)
_inf = float("-inf")


def register_analyzer(topic, cls):
    """ Register a new analyzer class for a particular topic of analysis.
    """
    registry[topic][cls.__name__] = cls


class AnalyzerFactory(object):
    """ Factory helper to find analyzers for a document.
    """
    @classmethod
    def for_document(cls, topic, document):
        """ Find an appropriate finder for this document.
        """
        return cls.for_locale(topic, country=document.country, locality=document.locality, language=document.language)

    @classmethod
    def for_locale(cls, topic, country=None, language=None, locality=None):
        """ Find an appropriate finder for this locale description. Tightest match wins.
        """
        analyzers = registry[topic]
        target = (country, language, locality)

        matches = ((finder, finder.locale_match(target)) for finder in analyzers.itervalues())
        matches = [(f, m) for f, m in matches if m]
        # best match
        matches.sort()

        # create and return an instance of the analyzer
        return matches[0][0]() if matches else None


class LocaleBasedAnalyzer(object):
    """ Mixin to support locale-based analyser lookup.
    """

    locale = (None, None, None)
    """ Locale for this analyzer, as a tuple: (country, language, locality). None matches anything."""

    @classmethod
    def locale_match(cls, target):
        """ Return a tuple ranking the match of `target` to this analyzer.
        """
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

analyzers = AnalyzerFactory()
