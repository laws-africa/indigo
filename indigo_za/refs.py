import re

from indigo.analysis.refs.base import BaseRefsFinder
from indigo.plugins import plugins


@plugins.register('refs')
class RefsFinderENG(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Act 52 of 2001
        Act no. 52 of 1998
        Constitution [of [the Republic of] South Africa] [Act][,] [1996]

    """

    # country, language, locality
    locale = (None, 'eng', None)

    act_re = re.compile(r'\bAct,?\s+([nN]o\.?\s*)?(\d+)+\s+of\s+(\d{4})|\bConstitution\b(\s+of(\s+the\s+Republic\s+of)?\s+South\s+Africa)?((\s+Act)?,?\s+1996)?')
    candidate_xpath = ".//text()[(contains(., 'Act') or contains(., 'Constitution')) and not(ancestor::a:ref)]"

    def make_href(self, match):
        if 'Constitution' in match.group(0):
            return '/za/act/1996/constitution'
        elif self.frbr_uri.country == 'za' and match.group(3) == '1996' and match.group(2) == '108':
            # Act 108 of 1996 was originally the constitution
            return '/za/act/1996/constitution'
        else:
            return '/%s/act/%s/%s' % (self.frbr_uri.country, match.group(3), match.group(2))


@plugins.register('refs')
class RefsFinderAFR(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Wet 52 van 2001
        Wet no. 52 van 1998
        Grondwet [van [die Republiek van] Suid-Afrika] [Wet][,] [1996]

    """

    # country, language, locality
    locale = (None, 'afr', None)

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
