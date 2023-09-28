import re

from indigo.analysis.terms.base import BaseTermsFinder
from indigo.plugins import plugins


@plugins.register('terms')
class TermsFinderENG(BaseTermsFinder):
    """ Finds references to defined terms in documents.

    This looks for heading elements with the words 'definitions' or 'interpretation',
    and then looks for phrases like

      "this word" means something...

    by looking for words in quotes at the start of the line.
    """

    # country, language, locality
    locale = (None, 'eng', None)

    heading_re = re.compile(r'.*(definition|interpretation)', re.IGNORECASE)
    quote_pairs = [('"', '"'), ("'", "'"), ('“', '”'), ('‘', '’'), ('«', '»')]
    # subclasses can define specific other patterns to be joined on | during compiling of term_re
    others = []

    def setup(self, doc):
        in_quotes = [fr'^\s*{x}(.+?){y}' for x, y in self.quote_pairs]
        self.term_re = re.compile('|'.join(in_quotes + self.others))
        super().setup(doc)


@plugins.register('terms')
class TermsFinderAFR(TermsFinderENG):
    """ Finds references to defined terms in documents.

    This looks for heading elements with the words 'definitions' or 'interpretation',
    and then looks for phrases like

      "gelisensieerde perseel" beteken die perseel...

    by looking for words in quotes at the start of the line.
    """

    # country, language, locality
    locale = (None, 'afr', None)

    heading_re = re.compile(r'woordbepaling|woordomskrywing|woordomskrywings', re.IGNORECASE)
