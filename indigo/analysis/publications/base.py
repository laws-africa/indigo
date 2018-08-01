from indigo.plugins import LocaleBasedMatcher


class BasePublicationFinder(LocaleBasedMatcher):
    """ This finds publication details for a published document. For example,
    a country-specific implementation can lookup a Government Gazette given
    a date, gazette name, and number.
    """

    locale = (None, None, None)
    """ The locale this finder is suited for, as ``(country, language, locality)``.
    """

    def find_publications(self, params):
        """ Return a list of publications matching the given params, a dict of arbitrary
        key-value pairs.
        """
        raise NotImplemented()
