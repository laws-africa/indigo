from lxml import etree
import re

from django.conf import settings

from docpipe.citations import ActMatcher
from docpipe.matchers import CitationMatcher
from indigo.analysis.markup import TextPatternMarker
from indigo.analysis.matchers import DocumentPatternMatcherMixin
from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Subtype, Work, Country


def markup_document_refs(document):
    # TODO: these are both old and should be retired
    finder = plugins.for_document('refs', document)
    if finder:
        finder.find_references_in_document(document)

    finder = plugins.for_document('refs-subtypes', document)
    if finder:
        finder.find_references_in_document(document)

    # new mechanism for calling locale-based matchers based on DocumentPatternMatcher
    for plugin_type in settings.INDIGO['LINK_REFERENCES_PLUGINS']:
        matcher = plugins.for_document(plugin_type, document)
        if matcher:
            matcher.markup_document_matches(document)


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


class ActNumberCitationMatcher(DocumentPatternMatcherMixin, ActMatcher):
    """Base plugin class for Act number citation matchers."""
    pass


@plugins.register('refs-act-numbers')
class ActNumberCitationMatcherENG(ActNumberCitationMatcher):
    locale = (None, 'eng', None)


@plugins.register('refs-act-numbers')
class ActNumberCitationMatcherFRA(ActNumberCitationMatcher):
    """ French Act number citation matcher.

    Loi 852 de 1998
    """
    locale = (None, 'fra', None)
    pattern_re = re.compile(
        r"""\bLoi\s*
            (?P<ref>
              (?P<num>\d+)\s*
              de\s*
              (?P<year>\d{4})
            )
        """,
        re.X | re.I)
    html_candidate_xpath = ".//text()[contains(., 'Loi') and not(ancestor::a)]"
    xml_candidate_xpath = ".//text()[contains(., 'Loi') and not(ancestor::ns:ref)]"


@plugins.register('refs-subtypes')
class RefsFinderSubtypesENG(BaseRefsFinder):
    """ Finds references to works other than Acts in documents, of the form:

        P 52 of 2001
        Ordinance no. 52 of 1998
        GN 1/2009

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
        self.subtypes = [s for s in Subtype.objects.all()]
        self.subtype_names = [s.name for s in self.subtypes]
        self.subtype_abbreviations = [s.abbreviation for s in self.subtypes]

        self.subtypes_string = '|'.join([re.escape(s) for s in self.subtype_names + self.subtype_abbreviations])

    def setup_candidate_xpath(self):
        xpath_contains = " or ".join([f"contains(translate(., '{subtype.upper()}', '{subtype.lower()}'), "
                                      f"'{subtype.lower()}')"
                                      for subtype in self.subtype_names + self.subtype_abbreviations])
        self.candidate_xpath = f".//text()[({xpath_contains}) and not(ancestor::a:ref)]"

    def setup_pattern_re(self):
        # TODO: disregard e.g. "6 May" in "GN 34 of 6 May 2020", but catch reference
        self.pattern_re = re.compile(
            fr'''
                (?P<ref>
                    (?P<subtype>{self.subtypes_string})\s*
                    (No\.?\s*)?
                    (?P<num>\d+)
                    (\s+of\s+|/)
                    (?P<year>\d{{4}})
                )
            ''', re.X | re.I)

    def markup_patterns(self, root):
        # don't do anything if there are no subtypes
        if self.subtypes:
            super().markup_patterns(root)

    def make_href(self, match):
        # use correct subtype for FRBR URI
        subtype = match.group('subtype')
        for s in self.subtypes:
            if subtype.lower() == s.name.lower() or subtype.lower() == s.abbreviation.lower():
                subtype = s.abbreviation
                break

        place = f'{self.frbr_uri.country}'
        if self.frbr_uri.locality:
            place = f'{self.frbr_uri.country}-{self.frbr_uri.locality}'

        return f'/akn/{place}/act/{subtype}/{match.group("year")}/{match.group("num")}'


@plugins.register('refs-cap')
class RefsFinderCapENG(DocumentPatternMatcherMixin, CitationMatcher):
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
    html_candidate_xpath = ".//text()[contains(., 'Cap') and not(ancestor::a)]"
    xml_candidate_xpath = ".//text()[contains(., 'Cap') and not(ancestor::ns:ref)]"

    def setup(self, frbr_uri, *args, **kwargs):
        super().setup(frbr_uri, *args, **kwargs)
        self.setup_cap_numbers(frbr_uri)

    def setup_cap_numbers(self, frbr_uri):
        try:
            country = Country.for_code(frbr_uri.country)
        except Country.DoesNotExist:
            return

        # look for a locality, but allow no matches
        locality = None
        if frbr_uri.locality:
            locality = country.localities.filter(code=frbr_uri.locality).first()

        place = locality or country
        cap_strings = [p for p in place.settings.work_properties if p.startswith('cap')]
        self.cap_numbers = {
            w.properties[c]: w.frbr_uri
            for c in cap_strings
            for w in Work.objects.filter(country=country, locality=locality)
            if w.properties.get(c)
        }

    def make_href(self, match):
        return self.cap_numbers.get(match.groups['num'])
