from lxml import etree
import re

from indigo.analysis.markup import TextPatternMarker
from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Subtype, Work


class BaseRefsFinder(LocaleBasedMatcher, TextPatternMarker):
    """ Finds references to Acts in documents.
    """
    marker_tag = 'ref'

    def find_references_in_document(self, document):
        """ Find references in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content.encode('utf-8'))
        self.document = document
        self.frbr_uri = document.doc.frbr_uri
        self.setup(root)
        self.markup_patterns(root)
        document.content = etree.tostring(root, encoding='unicode')

    def is_valid(self, node, match):
        if self.make_href(match) != self.frbr_uri.work_uri():
            return True

    def markup_match(self, node, match):
        """ Markup the match with a ref tag. The first group in the match is substituted with the ref.
        """
        ref = etree.Element(self.marker_tag)
        ref.text = match.group('ref')
        ref.set('href', self.make_href(match))
        return ref, match.start('ref'), match.end('ref')

    def make_href(self, match):
        """ Turn this match into a full FRBR URI href.
            Check for an existing Act with that FRBR URI in the locality first; default to national (may or may not exist).
        """
        link_uri = f"/akn/{self.frbr_uri.country}/act/{match.group('year')}/{match.group('num')}"
        if self.frbr_uri.locality:
            local = f"/akn/{self.frbr_uri.country}-{self.frbr_uri.locality}/act/{match.group('year')}/{match.group('num')}"
            if Work.objects.filter(frbr_uri=local).exists():
                link_uri = local

        return link_uri


@plugins.register('refs')
class RefsFinderENG(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Act 52 of 2001
        Act no. 52 of 1998
        Income Tax Act, 1962 (No 58 of 1962)

    """

    # country, language, locality
    locale = (None, 'eng', None)

    pattern_re = re.compile(
        r'''\bAct,?\s+
            (\d{4}\s+)?
            \(?
            (?P<ref>
             ([nN]o\.?\s*)?
             (?P<num>\d+)\s+
             of\s+
             (?P<year>\d{4})
            )
        ''', re.X)
    candidate_xpath = ".//text()[contains(., 'Act') and not(ancestor::a:ref)]"


@plugins.register('refs-subtypes')
class RefsFinderSubtypesENG(BaseRefsFinder):
    """ Finds references to works other than Acts in documents, of the form:

        P 52 of 2001
        Ordinance no. 52 of 1998
        GN 1/2009
        General Notice 12 published in Gazette 12345 of 2019

    """

    # country, language, locality
    locale = (None, 'eng', None)

    def setup(self, root):
        self.setup_subtypes()
        self.setup_candidate_xpath()
        self.setup_pattern_re()
        # If we don't have subtypes, don't let the superclass do setup, because it will fail.
        # We're going to opt-out of doing any work anyway.
        if self.subtypes:
            super().setup(root)

    def setup_subtypes(self):
        self.full_subtypes = Subtype.objects.all()
        self.subtypes = [s.name for s in self.full_subtypes] + \
                        [s.abbreviation for s in self.full_subtypes]

    def setup_candidate_xpath(self):
        xpath_contains = " or ".join(
            [f"contains(translate(., '{s.upper()}', '{s.lower()}'), "
             f"'{s.lower()}')"
             for s in self.subtypes])
        self.candidate_xpath = f".//text()[({xpath_contains}) and not(ancestor::a:ref)]"

    def setup_pattern_re(self):
        subtypes_for_re = '|'.join([re.escape(s) for s in self.subtypes])
        self.pattern_re = re.compile(
            fr'''
                (?P<ref>
                    (?P<subtype>{subtypes_for_re})\s*
                    (No\.?\s*)?
                    (?P<num>\d+)
                    .{{0,60}}(\s|/)
                    (?P<year>\d{{4}})\b
                )
            ''', re.X | re.I)

    def markup_patterns(self, root):
        # don't do anything if there are no subtypes
        if self.subtypes:
            super().markup_patterns(root)

    def make_href(self, match):
        # use correct subtype for FRBR URI
        subtype = match.group('subtype').lower()
        subtype_for_uri = None
        for s in self.full_subtypes:
            if subtype == s.name.lower() or subtype == s.abbreviation.lower():
                subtype_for_uri = s.abbreviation
                break

        place = f'{self.frbr_uri.country}'
        if self.frbr_uri.locality:
            place = f'{self.frbr_uri.country}-{self.frbr_uri.locality}'

        if subtype_for_uri:
            return f'/akn/{place}/act/{subtype_for_uri}/{match.group("year")}/{match.group("num")}'


@plugins.register('refs-cap')
class RefsFinderCapENG(BaseRefsFinder):
    """ Finds references to works with cap numbers, of the form:

        Cap. 231
        Cap A4

    """
    # country, language, locality
    locale = (None, 'eng', None)

    pattern_re = re.compile(
        r'''
            (?P<ref>
             \bCap\.?\s*
             (?P<num>\w+)
            )
        ''', re.X)
    candidate_xpath = ".//text()[contains(., 'Cap') and not(ancestor::a:ref)]"

    def setup(self, root):
        self.setup_cap_numbers(self.document)
        super().setup(root)

    def setup_cap_numbers(self, document):
        country = document.work.country
        locality = document.work.locality
        place = locality or country
        cap_strings = [p for p in place.settings.work_properties if p.startswith('cap')]

        self.cap_numbers = {w.properties[c]: w.frbr_uri for c in cap_strings for w in Work.objects.filter(country=country, locality=locality) if w.properties.get(c)}

    def is_valid(self, node, match):
        return self.cap_numbers.get(match.group('num'))

    def make_href(self, match):
        return self.cap_numbers[match.group('num')]
