import re
from lxml import etree

from indigo.analysis.refs.base import BaseRefsFinder
from indigo.plugins import plugins


@plugins.register('refs')
class RefsFinderENGza(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Act 52 of 2001
        Act no. 52 of 1998
        Income Tax Act, 1962 (No 58 of 1962)
        Constitution [of [the Republic of] South Africa] [Act][,] [1996]

        If not in South Africa ('za'), should default to indigo/analysis/refs/global.py (doesn't include 'Constitution')

    """

    # country, language, locality
    locale = ('za', 'eng', None)

    # if Act part changes, update indigo/analysis/refs/global.py
    act_re = re.compile(
        r'\b(Act,?\s+(\d{4}\s+)?\(?(([nN]o\.?\s*)?(\d+)\s+of\s+(\d{4})))|\bConstitution\b(\s+of(\s+the\s+Republic\s+of)?\s+South\s+Africa)?((\s+Act)?,?\s+1996)?'
    )
    candidate_xpath = ".//text()[(contains(., 'Act') or contains(., 'Constitution')) and not(ancestor::a:ref)]"

    def make_href(self, match):
        year = match.group(6)
        number = match.group(5)
        if 'Constitution' in match.group(0):
            return '/za/act/1996/constitution'
        elif self.frbr_uri.country == 'za' and year == '1996' and number == '108':
            # the Constitution was originally Act 108 of 1996
            return '/za/act/1996/constitution'
        else:
            return '/%s/act/%s/%s' % (self.frbr_uri.country, year, number)

    def make_ref(self, match):
        if 'Constitution' in match.group(0):
            group = 0
        elif match.group(2):
            group = 3
        else:
            group = 1

        ref = etree.Element(self.ref_tag)
        ref.text = match.group(group)
        ref.set('href', self.make_href(match))
        return (ref, match.start(group), match.end(group))


@plugins.register('refs')
class RefsFinderAFRza(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Wet 52 van 2001
        Wet no. 52 van 1998
        Grondwet [van [die Republiek van] Suid-Afrika] [Wet][,] [1996]

    """

    # country, language, locality
    locale = ('za', 'afr', None)

    act_re = re.compile(r'\bWet,?\s+([nN]o\.?\s*)?(\d+)+\s+van\s+(\d{4})|\bGrondwet\b(\s+van(\s+die\s+Republiek\s+van)?\s+Suid[- ]Afrika)?((\s+Wet)?,?\s+1996)?')
    candidate_xpath = ".//text()[(contains(., 'Wet') or contains(., 'Grondwet')) and not(ancestor::a:ref)]"

    def make_href(self, match):
        if 'Grondwet' in match.group(0):
            return '/za/act/1996/constitution'
        elif self.frbr_uri.country == 'za' and match.group(3) == '1996' and match.group(2) == '108':
            # Act 108 of 1996 was originally the constitution
            return '/za/act/1996/constitution'
        else:
            return '/%s/act/%s/%s' % (self.frbr_uri.country, match.group(3), match.group(2))
