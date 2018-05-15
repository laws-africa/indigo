from indigo_api.importers.base import Importer
from indigo_api.importers.registry import importers


@importers.register
class ImporterPL(Importer):
    """ Importer for the Polish tradition.
    """
    locale = ('pl', None, None)

    slaw_grammar = 'pl'

    def reformat_text(self, text):
        # TODO: do something intelligent
        return text
