from indigo.plugins import plugins


class ResolvedAnchor(object):
    """ An anchor that has been resolved into a point in a document.
    """
    element = None
    toc_entry = None
    is_toc_element = False

    def __init__(self, anchor, document):
        self.anchor = anchor
        self.document = document

        self.resolve()

    def resolve(self):
        anchor_id = self.anchor['id']

        if '/' in anchor_id:
            component, anchor_id = anchor_id.split('/', 1)
        else:
            component = 'main'

        component = self.document.doc.components().get(component)
        if component is None:
            return

        anchor_id = anchor_id.replace("'", "\'")
        elems = component.xpath("//*[@id='%s']" % anchor_id)
        if elems:
            self.resolve_element(elems[0])
        elif anchor_id in ['preface', 'preamble']:
            # HACK HACK HACK
            # We sometimes use 'preamble' and 'preface' even though they aren't IDs
            elems = component.xpath("//a:%s" % anchor_id, namespaces={'a': self.document.doc.namespace})
            if elems:
                self.resolve_element(elems[0])

    def resolve_element(self, element):
        self.element = element

        # lookup TOC information
        builder = plugins.for_document('toc', self.document)
        if builder:
            self.toc_entry = builder.table_of_contents_entry_for_element(self.document, self.element)
            self.is_toc_element = self.toc_entry.element == self.element

    def element_html(self):
        if not self.element:
            return None

        return self.document.element_to_html(self.element)

    def toc_element_html(self):
        if not self.toc_entry:
            return None

        return self.document.element_to_html(self.toc_entry.element)
