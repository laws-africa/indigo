class ImporterFactory(object):
    """ Helper object to lookup and create importers for documents
    based on locale information.
    """
    registry = {}

    def for_locale(self, country=None, language=None, locality=None):
        """ Find an appropriate importer for this locale description. Tightest match wins.
        """
        target = (country, language, locality)

        matches = ((cls, cls.locale_match(target)) for cls in self.registry.itervalues())
        matches = [(f, m) for f, m in matches if m]

        matches = [(i, score) for i, score in matches if score]
        # sort by score, best match last
        matches.sort(key=lambda x: x[1])
        match = matches[-1][0]

        # create and return an instance of the analyzer
        return match() if matches else None

    def register(self, cls):
        """ Register a new import class with the registry.
        """
        self.registry[cls.__name__] = cls
        return cls

importers = ImporterFactory()
