import re

import unicodedata
from lxml import etree

from indigo.plugins import LocaleBasedMatcher, plugins


@plugins.register('sentence-caser')
class BaseSentenceCaser(LocaleBasedMatcher):
    """ Sentence cases headings in a document.
    """
    terms = None
    normalized_terms = None

    def sentence_case_headings_in_document(self, document):
        accented_terms = document.language.accented_terms.first()
        self.terms = accented_terms.terms if accented_terms else []
        self.terms.sort(key=lambda x: len(x), reverse=True)
        self.normalized_terms = [''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn').lower()
                                 for t in self.terms]
        root = etree.fromstring(document.content.encode('utf-8'))
        nsmap = {'a': root.nsmap[None]}
        for heading in root.xpath('//a:heading', namespaces=nsmap):
            self.capitalized = False
            skip_elements = heading.xpath(".//a:*[ancestor::a:authorialNote]", namespaces=nsmap)
            for elem in heading.iter():
                if elem in skip_elements:
                    continue
                elem.text = self.adjust_heading_text(elem.text)
                elem.tail = self.adjust_heading_text(elem.tail)

        document.content = etree.tostring(root, encoding='unicode')

    def adjust_heading_text(self, text):
        # text may be None or ' ', for example -- ignore in those cases
        if text and text.strip():
            text = self.apply_terms(text.lower())
            if not self.capitalized:
                # don't use capitalize() on the whole of `text`, as this interferes with capitalised terms
                # either way, lstrip if capitalizing here since the first letter would be missed otherwise
                text = text.lstrip()[0].upper() + (text.lstrip()[1:] if len(text.lstrip()) > 1 else '')
                self.capitalized = True
        return text

    def apply_terms(self, text):
        # save a tiny bit of time by checking for any matches first
        if any(t in text for t in self.normalized_terms):
            for i, term in enumerate(self.normalized_terms):
                text = re.sub(rf'\b{term}\b', self.terms[i], text)
        return text
