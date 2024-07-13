import re

from django.db.models import Q

from cobalt import FrbrUri
from docpipe.matchers import CitationMatcher
from indigo.analysis.matchers import DocumentPatternMatcherMixin
from indigo.plugins import plugins
from indigo_api.models import Document, Country, Work


class CommonTitlesCitationMatcher(DocumentPatternMatcherMixin, CitationMatcher):
    """Finds references to works based "the XXX Act" patterns. """
    # only supports English
    locale = (None, 'eng', None)

    html_candidate_xpath = ".//text()[contains(., ' the ') and contains(., ' Act') and not(ancestor::a)]"
    xml_candidate_path = ".//text()[contains(., ' the ') and contains(., ' Act') and not(ancestor::ns:ref)]"

    pattern_re = re.compile(r'\b(?P<pre>the\s+(?P<title>((?!the)\S+\s+){1,7})Act)\s*,?(\s*of\s+)?\s*(?P<year>[12][0-9]{3})?\b')

    # map from titles to FRBR URIs
    titles = None

    def setup(self, frbr_uri, text=None, root=None):
        self.setup_titles(frbr_uri)
        super().setup(frbr_uri, text, root)

    def setup_titles(self, frbr_uri):
        self.titles = self.titles.get(frbr_uri.place) or self.titles.get(frbr_uri.country) or {}

    def extract_paged_text_matches(self):
        if self.titles:
            super().extract_paged_text_matches()

    def run_dom_matching(self):
        if self.titles:
            super().run_dom_matching()

    def make_href(self, match):
        # normalise whitespace in the title
        title = ' '.join(match.groups['title'].split()) + ' Act'
        year = match.groups['year']

        if title in self.titles:
            frbr_uri = self.titles[title]

            if year:
                uri = FrbrUri.parse(frbr_uri)
                if not uri.date.startswith(year):
                    frbr_uri = None
            else:
                # the match has more text than we want to mark up, so reduce to just the title
                match.text = match.groups['pre']
                match.end = match.start + len(match.text)

            return frbr_uri


@plugins.register('refs-act-names')
class WorkTitlesCitationMatcher(CommonTitlesCitationMatcher):
    def setup_titles(self, frbr_uri):
        self.titles = {}

        country = Country.objects.filter(country__pk=frbr_uri.country.upper()).first()
        if country:
            locality = None
            if frbr_uri.locality:
                locality = country.localities.filter(code=frbr_uri.locality).first()

            qs = self.get_queryset(frbr_uri, country, locality)

            # a work can't cite something published in the future
            date = frbr_uri.expression_date
            if date and date.startswith('@'):
                qs = qs.filter(date__lte=date[1:5])

            for we in qs:
                self.titles[we["title"]] = we["frbr_uri"]

    def get_queryset(self, frbr_uri, country, locality):
        # load titles for WorkExpressions in this country and/or locality
        qs = (
            Work.objects.filter(
                country=country,
                # we only want principal Acts
                principal=True,
                doctype='act',
                subtype=None,
                work_in_progress=False,
            )
            .values("frbr_uri", "title")
        )

        if frbr_uri.locality and locality:
            qs = qs.filter(Q(locality__isnull=True) | Q(locality=locality))
        else:
            qs = qs.filter(locality__isnull=True)

        return qs

