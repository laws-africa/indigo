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

    def markup_element_matches(self, document, element):
        """Markup matches only inside ``element``.

        ``element`` must be an editable etree element and may be attached to a
        larger XML tree. This lets matchers inspect its ancestors and siblings
        while limiting candidate text to the supplied subtree. Unlike
        :meth:`markup_document_matches`, this method does not update
        ``document.content``.
        """
        ancestor_xpath = self.xml_ancestor_xpath
        try:
            # TextPatternMatcher normally anchors XML matching at body-like
            # elements. For a scoped run, the supplied element is the anchor.
            self.xml_ancestor_xpath = None
            self.markup_xml_matches(document.doc.frbr_uri, element)
        finally:
            self.xml_ancestor_xpath = ancestor_xpath
