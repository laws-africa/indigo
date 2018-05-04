# -*- coding: utf-8 -*-

import logging
import re

from indigo_analysis.terms.base import BaseTermsFinder

log = logging.getLogger(__name__)


class TermsFinderEN(BaseTermsFinder):
    """ Finds references to defined terms in documents.

    This looks for heading elements with the words 'definitions' or 'interpretation',
    and then looks for phrases like

      "this word" means something...

    by looking for words in quotes at the start of the line.
    """

    # country, language, locality
    locale = (None, 'eng', None)

    heading_re = re.compile(r'definition|interpretation', re.IGNORECASE)
    term_re = re.compile(r'^\s*["“”](.+?)["“”]')
