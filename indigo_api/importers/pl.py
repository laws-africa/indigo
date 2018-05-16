# -*- coding: utf-8 -*-
from indigo_api.importers.base import Importer
from indigo_api.importers.registry import importers
import re

@importers.register
class ImporterPL(Importer):
    """ Importer for the Polish tradition.
    """
    locale = ('pl', None, None)

    slaw_grammar = 'pl'

    def reformat_text(self, text):
        # Join hyphenated words - ones that have been split in middle b/c of line end.   
        text = re.sub(ur"([a-ząćęłńśóźż])-\n([a-ząćęłńśóźż])", "\g<1>\g<2>", text)
        # Remove all line breaks, except when the new line starts with a symbol known
        # to be the start of a division.
        text = re.sub(ur"\n(?!("
                      u"DZIAŁ [IVXLC]|"
                      u"Rozdział [IVXLC1-9]|"
                      u"Art\.|"
                      u"§ \d+[a-z]*\.|"
                      u"\d+[a-z]*\.|"
                      u"\d+[a-z]*\)|"
                      u"[a-z]+\)|"
                      u"–))", " ", text)
        return text
