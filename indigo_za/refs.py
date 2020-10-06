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

    # if Act part changes, you may also want to update indigo/analysis/refs/global.py
    pattern_re = re.compile(
        r'''\b
            (
             Act,?\s+(\d{4}\s+)?                    # Act   or   Act, 1998
              \(?                                   # Tax Act, 1962 (No 58 of 1962)
              (?P<ref>
               ([nN]o\.?\s*)?(?P<num>\d+)\s+of\s+(?P<year>\d{4})   # no. NN of NNNN
                                                    #     NN of NNNN
              )
            )
            |
            \bConstitution\b(\s+of(\s+the\s+Republic\s+of)?\s+South\s+Africa)?((\s+Act)?,?\s+1996)?
        ''', re.X)
    candidate_xpath = ".//text()[(contains(., 'Act') or contains(., 'Constitution')) and not(ancestor::a:ref)]"

    constitution = 'Constitution'

    def is_constitution(self, match):
        # the Constitution was originally Act 108 of 1996
        return self.constitution in match.group(0) or \
               (self.frbr_uri.country == 'za' and match.group('year') == '1996' and match.group('num') == '108')

    def make_href(self, match):
        if self.is_constitution(match):
            return '/akn/za/act/1996/constitution'

        return super().make_href(match)

    def markup_match(self, node, match):
        if self.constitution in match.group(0):
            group = 0
        elif match.group(2):
            group = 3
        else:
            group = 1

        ref = etree.Element(self.marker_tag)
        ref.text = match.group(group)
        ref.set('href', self.make_href(match))
        return ref, match.start(group), match.end(group)


@plugins.register('refs')
class RefsFinderAFRza(RefsFinderENGza):
    """ Finds references to Acts in documents, of the form:

        Wet 52 van 2001
        Wet no. 52 van 1998
        Grondwet [van [die Republiek van] Suid-Afrika] [Wet][,] [1996]

    """

    # country, language, locality
    locale = ('za', 'afr', None)

    pattern_re = re.compile(
        r'''\b
            (?P<ref>
             Wet,?\s+([nN]o\.?\s*)?
             (
              (?P<num>\d+)+\s+van\s+(?P<year>\d{4})
             )
            )
            |
            \bGrondwet\b(\s+van(\s+die\s+Republiek\s+van)?\s+Suid[- ]Afrika)?((\s+Wet)?,?\s+1996)?
    ''', re.X)
    candidate_xpath = ".//text()[(contains(., 'Wet') or contains(., 'Grondwet')) and not(ancestor::a:ref)]"

    constitution = 'Grondwet'

    def markup_match(self, node, match):
        if self.constitution in match.group(0):
            group = 0
        else:
            group = 'ref'

        ref = etree.Element(self.marker_tag)
        ref.text = match.group(group)
        ref.set('href', self.make_href(match))
        return ref, match.start(group), match.end(group)
