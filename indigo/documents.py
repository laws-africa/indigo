from indigo.plugins import plugins


class ResolvedAnchor(object):
    """ An anchor that has been resolved into a point in a document.
    """
    element = None
    toc_entry = None

    def __init__(self, anchor, document):
        self.anchor = anchor
        self.document = document

        self.resolve()

    def resolve(self):
        anchor_id = self.anchor['id']
        root = self.document.doc.root

        elems = root.xpath("//*[@id='%s']" % anchor_id.replace("'", "\'"))
        if elems:
            self.resolve_element(elems[0])

    def resolve_element(self, element):
        self.element = element

        # lookup TOC information
        builder = plugins.for_document('toc', self.document)
        if builder:
            self.toc_entry = builder.table_of_contents_entry_for_element(self.document, self.element)

    def element_html(self):
        if not self.element:
            return None

        return self.document.element_to_html(self.element)
