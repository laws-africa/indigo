class ResolvedAnchor(object):
    """ An anchor that has been resolved into a point in a document.
    """
    element = None
    title = None

    def __init__(self, anchor, document):
        self.anchor = anchor
        self.document = document

        self.resolve()

    def resolve(self):
        anchor_id = self.anchor['id']
        root = self.document.doc.root

        elems = root.xpath("//*[@id='%s']" % anchor_id.replace("'", "\'"))
        if elems:
            self.element = elems[0]
            # TODO: find closest parent item in the table of contents, and stash that along with
            # its title
        else:
            self.element = None

    def element_html(self):
        if not self.element:
            return None

        return self.document.element_to_html(self.element)
