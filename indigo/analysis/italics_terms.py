from lxml import etree
import re

from indigo.analysis.markup import TextPatternMarker
from indigo.plugins import LocaleBasedMatcher, plugins


@plugins.register('italics-terms')
class BaseItalicsFinder(LocaleBasedMatcher, TextPatternMarker):
    """ Italicises terms in a document.
    """
    marker_tag = 'i'

    def mark_up_italics_in_document(self, document, italics_terms):
        """ Find and italicise terms in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content.encode('utf-8'))
        self.setup_candidate_xpath(italics_terms)
        self.setup_pattern_re(italics_terms)
        self.setup(root)
        self.markup_patterns(root)
        document.content = etree.tostring(root, encoding='unicode')

    def setup_candidate_xpath(self, terms):
        xpath_contains = ' or '.join([f'contains(., "{term}")' for term in [partial for t in terms for partial in t.split('"')]])
        self.candidate_xpath = f'.//text()[({xpath_contains}) and not(ancestor::a:i)]'

    def setup_pattern_re(self, terms):
        # first, sort longest to shortest, so that e.g. 'ad idem' is marked up before 'ad'
        terms = sorted(terms, key=len, reverse=True)
        terms = [t.strip() for t in terms]
        terms = [re.escape(t) for t in terms if t]
        terms = '|'.join(terms)
        terms = fr'\b({terms})\b'

        self.pattern_re = re.compile(terms)

    def markup_match(self, node, match):
        """ Markup the match with a <i> tag.
        """
        italics_term = etree.Element(self.marker_tag)
        italics_term.text = match.group()
        return italics_term, match.start(), match.end()
