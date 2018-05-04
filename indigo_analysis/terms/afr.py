# -*- coding: utf-8 -*-

import logging
import re

from indigo_analysis.terms.eng import TermsFinderENG

log = logging.getLogger(__name__)


class TermsFinderAFR(TermsFinderENG):
    """ Finds references to defined terms in documents.

    This looks for heading elements with the words 'definitions' or 'interpretation',
    and then looks for phrases like

      "gelisensieerde perseel" beteken die perseel...

    by looking for words in quotes at the start of the line.
    """

    # country, language, locality
    locale = (None, 'afr', None)

    heading_re = re.compile(r'woordbepaling', re.IGNORECASE)
