import re

from .base import BaseRefsFinder


class RefsFinderEN(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Act 52 of 2001
        Act no. 52 of 1998
    """

    # country, language, locality
    locale = (None, 'eng', None)

    act_re = re.compile(r'Act,?\s+(no\.?\s*)?(\d+)+\s+of\s+(\d{4})', re.I)
    candidate_xpath = ".//text()[contains(., 'Act') and not(ancestor::a:ref)]"

    def make_href(self, match):
        return '/%s/act/%s/%s' % (self.frbr_uri.country, match.group(3), match.group(2))
