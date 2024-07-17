from lxml import etree

from indigo.plugins import LocaleBasedMatcher


class DocumentPatternMatcherMixin(LocaleBasedMatcher):
    """Mixin for making a TextPatternMatcher work with Indigo Document objects and Indigo's locale-based plugins.
    """

    def markup_document_matches(self, document):
        """ Markup matches in an Indigo document object and update the XML in place.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root, we have to re-parse it
        root = etree.fromstring(document.content.encode('utf-8'))
        self.markup_xml_matches(document.doc.frbr_uri, root)
        document.content = etree.tostring(root, encoding='unicode')
