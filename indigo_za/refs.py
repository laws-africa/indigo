import re

from indigo.analysis.refs.base import BaseRefsFinder
from indigo.plugins import plugins


@plugins.register('refs')
class RefsFinderENG(BaseRefsFinder):
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


@plugins.register('refs')
class RefsFinderAFR(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Wet 52 van 2001
        Wet no. 52 van 1998
    """

    # country, language, locality
    locale = (None, 'afr', None)

    act_re = re.compile(r'Wet,?\s+(no\.?\s*)?(\d+)+\s+van\s+(\d{4})', re.I)
    candidate_xpath = ".//text()[contains(., 'Wet') and not(ancestor::a:ref)]"

    def make_href(self, match):
        return '/%s/act/%s/%s' % (self.frbr_uri.country, match.group(3), match.group(2))
