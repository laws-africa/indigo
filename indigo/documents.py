from indigo.plugins import plugins


class ResolvedAnchor(object):
    """ An anchor that has been resolved into a point in a document.
    """
    element = None
    toc_entry = None
    is_toc_element = False
    exact_match = False

    def __init__(self, anchor_id, selectors, document, exact=False):
        """ Try to resolve a target (anchor + selectors) in a document. If exact is False (the default),
        then if the exact anchor can't be resolved, try to resolve as close as possible.
        The exact_match attribute will be set accordingly.

        Selectors are currently ignored because they apply to the rendered text, rather than the XML.
        """
        self.anchor_id = anchor_id
        self.selectors = selectors
        self.document = document

        self.resolve(exact)

    def resolve(self, exact):
        anchor_id = self.anchor_id
        component = self.document.doc.main
        self.exact_match = True

        while anchor_id:
            escaped = anchor_id.replace("'", "\\'")
            elems = component.xpath(f".//a:*[@eId='{escaped}']", namespaces={'a': self.document.doc.namespace})
            if len(elems):
                self.resolve_element(elems[0])
                break
            elif anchor_id in ['preface', 'preamble']:
                # HACK HACK HACK
                # We sometimes use 'preamble' and 'preface' even though they aren't IDs
                elems = component.xpath(f".//a:{escaped}", namespaces={'a': self.document.doc.namespace})
                if len(elems):
                    self.resolve_element(elems[0])
                    break

            # no match, try further up the anchor id chain
            if not exact and '__' in anchor_id:
                self.exact_match = False
                anchor_id = anchor_id.rsplit('__', 1)[0]
            else:
                # give up
                anchor_id = None

    def resolve_element(self, element):
        self.element = element

        # lookup TOC information
        builder = plugins.for_document('toc', self.document)
        if builder:
            self.toc_entry = builder.table_of_contents_entry_for_element(self.document, self.element)
            self.is_toc_element = self.toc_entry and self.toc_entry.element == self.element

    def element_html(self):
        if not self.element:
            return None

        return self.document.element_to_html(self.element)

    def toc_element_html(self):
        if not self.toc_entry:
            return None

        return self.document.element_to_html(self.toc_entry.element)

    def target(self):
        return {
            'anchor_id': self.anchor_id,
            'selectors': self.selectors,
        }
