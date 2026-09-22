import re

from django.conf import settings

from docpipe.citations import ActNoOfYearMatcher, ActYearNumberMatcher
from docpipe.matchers import CitationMatcher, ExtractedMatch
from indigo.analysis.matchers import DocumentPatternMatcherMixin
from indigo.plugins import plugins
from indigo_api.models import Subtype, Work, Country


def markup_document_refs(document):
    """Markup references throughout an Indigo Document."""
    markup_refs(document)


def markup_element_refs(document, element):
    """Markup references only inside ``element``, using its full tree as context.

    The editable etree element should be attached at its correct position in a
    complete document tree when internal references need surrounding structural
    context. The Indigo Document is used for locale, FRBR URI and remote-work
    lookups, but its content is not changed.
    """
    markup_refs(document, element)


def markup_refs(document, element=None):
    """Run the configured reference plugins in order."""
    for plugin_type in settings.INDIGO['LINK_REFERENCES_PLUGINS']:
        matcher = plugins.for_document(plugin_type, document)
        if matcher:
            if element is None:
                matcher.markup_document_matches(document)
            else:
                matcher.markup_element_matches(document, element)


class ActNumberCitationMatcher(DocumentPatternMatcherMixin, ActNoOfYearMatcher):
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


@plugins.register('refs-act-numbers')
class ActNumberCitationMatcherAFR(ActNumberCitationMatcher):
    """ Afrikaans Act number citation matcher.

    Wet 852 van 1998
    """
    locale = (None, 'afr', None)
    pattern_re = re.compile(
        r"""\bWet,?\s*
            ((19|20)\d{2}\s*)?
            \(?
            (?P<ref>
              ([no.]*\s*)?
              (?P<num>\d+)\s*
              van\s*
              (?P<year>\d{4})
            )\)?
        """,
        re.X | re.I)
    html_candidate_xpath = ".//text()[contains(., 'Wet') and not(ancestor::a)]"
    xml_candidate_xpath = ".//text()[contains(., 'Wet') and not(ancestor::ns:ref)]"


@plugins.register('refs-subtype-numbers')
class SubtypeNumberCitationMatcherENG(DocumentPatternMatcherMixin, CitationMatcher):
    """ Finds references to works based on subtypes, of the form:

        P 52 of 2001
        Ordinance no. 52 of 1998
        GN 1/2009

    """

    # country, language, locality
    locale = (None, 'eng', None)

    html_candidate_xpath = ".//text()[(PATTERNS) and not(ancestor::a)]"
    xml_candidate_xpath = ".//text()[(PATTERNS) and not(ancestor::ns:ref)]"

    def setup(self, *args, **kwargs):
        self.setup_subtypes()
        super().setup(*args, **kwargs)

    def setup_subtypes(self):
        self.subtypes = [s for s in Subtype.objects.all()]
        subtype_names = [s.name for s in self.subtypes]
        subtype_abbreviations = [s.abbreviation.upper() for s in self.subtypes]

        # sort, longest first
        subtypes = sorted(subtype_names + subtype_abbreviations, key=len, reverse=True)

        if self.candidate_xpath:
            # build the xpath; if there are no subtypes, use "false" to not match anything
            xpath_contains = " or ".join([
                f"contains(translate(., '{subtype.upper()}', '{subtype.lower()}'), '{subtype.lower()}')"
                for subtype in subtypes
            ]) or "false"
            self.candidate_xpath = self.candidate_xpath.replace('PATTERNS', xpath_contains)

        # TODO: disregard e.g. "6 May" in "GN 34 of 6 May 2020", but catch reference
        subtypes_string = '|'.join(re.escape(s) for s in subtypes)
        self.pattern_re = re.compile(
            fr'''
                (?P<ref>
                    \b(?P<subtype>{subtypes_string})\s+
                    ([nN]o\.?\s*)?
                    (?P<num>[a-zA-Z0-9-]+)
                    (\s+of\s+|/)
                    (?P<year>\d{{4}})
                )
            ''', re.X)

    def extract_paged_text_matches(self):
        # don't do anything if there are no subtypes
        if self.subtypes:
            super().extract_paged_text_matches()

    def run_dom_matching(self):
        # don't do anything if there are no subtypes
        if self.subtypes:
            super().run_dom_matching()

    def make_href(self, match: ExtractedMatch):
        # use correct subtype for FRBR URI
        subtype = match.groups['subtype']
        for s in self.subtypes:
            if subtype.lower() == s.name.lower() or subtype.lower() == s.abbreviation.lower():
                subtype = s.abbreviation
                break

        place = f'{self.frbr_uri.country}'
        if self.frbr_uri.locality:
            place = f'{self.frbr_uri.country}-{self.frbr_uri.locality}'

        return f'/akn/{place}/act/{subtype}/{match.groups["year"]}/{match.groups["num"].lower()}'


# TODO: no longer used in LINK_REFERENCES_PLUGINS; either update and add back in, or nuke
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


@plugins.register('refs-act-numbers-2')
class ActYearNumberCitationMatcherENG(DocumentPatternMatcherMixin, ActYearNumberMatcher):
    locale = (None, 'eng', None)


@plugins.register('refs-act-numbers-no-year')
class ActNumberCitationMatcherGH(ActYearNumberCitationMatcherENG):
    """Act number citation matching for Ghana, which uses a style that relies on their Act numbers being unique.
    The year must be looked up in the database.

    Example: Foo Act (Act 123)
    """
    locale = ('gh', 'eng', None)

    pattern_re = re.compile(r"\(\s*(?P<ref>Act\s*(?P<num>\d+)\s*)\)", re.I)

    def make_href(self, match: ExtractedMatch):
        num = match.groups["num"]
        return Work.objects.filter(
            country__country__pk=self.frbr_uri.country.upper(),
            locality=None,
            doctype="act",
            subtype=None,
            number=num,
        ).order_by("-date").values_list("frbr_uri", flat=True).first()
