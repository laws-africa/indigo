from lxml import etree

from indigo.xmlutils import wrap_text


class TextPatternMarker:
    """ Logic for marking up portions of text in a document using regular expressions.
    """

    pattern_re = None
    """ Compiled re pattern to be applied to the text return by nodes matching candidate_xpath.
    Must be defined by subclasses.
    """

    candidate_xpath = None
    """ Xpath for candidate text nodes that should be tested for matches. Must be defined by subclasses.
    """

    ancestors = ['coverpage', 'preface', 'preamble', 'body', 'mainBody', 'conclusions']
    """ Tags that the candidate_xpath should be run against.
    """

    marker_tag = 'b'
    """ Tag that will be used to markup matches.
    """

    def setup(self, root):
        self.ns = root.nsmap[None]
        self.nsmap = {'a': self.ns}
        self.marker_tag = "{%s}%s" % (self.ns, self.marker_tag)
        self.ancestor_xpath = etree.XPath('|'.join(f'.//a:{a}' for a in self.ancestors), namespaces=self.nsmap)
        self.candidate_xpath = etree.XPath(self.candidate_xpath, namespaces=self.nsmap)

    def markup_patterns(self, root):
        for ancestor in self.ancestor_nodes(root):
            for candidate in self.candidate_nodes(ancestor):
                node = candidate.getparent()

                if not candidate.is_tail:
                    # text directly inside a node
                    for match in self.find_matches(node.text):
                        new_node = self.handle_match(node, match, in_tail=False)
                        if new_node is not None:
                            # the node has now changed, making the offsets in any subsequent
                            # matches incorrect. so stop looking and start again, checking
                            # the tail of the newly inserted node
                            node = new_node
                            break

                while node is not None and node.tail:
                    for match in self.find_matches(node.tail):
                        new_node = self.handle_match(node, match, in_tail=True)
                        if new_node is not None:
                            # the node has now changed, making the offsets in any subsequent
                            # matches incorrect. so stop looking and start again, checking
                            # the tail of the newly inserted node
                            node = new_node
                            break
                    else:
                        # we didn't break out of the loop, so there are no valid matches, give up
                        node = None

    def find_matches(self, text):
        """ Return an iterable of matches in this chunk of text.
        """
        return self.pattern_re.finditer(text)

    def is_valid(self, node, match):
        return True

    def handle_match(self, node, match, in_tail):
        """ Process a match. If this modifies the text (or tail, if in_tail is True), then
        return the new node that should have its tail checked for further matches.
        Otherwise, return None.
        """
        if self.is_valid(node, match):
            ref, start_pos, end_pos = self.markup_match(node, match)
            return wrap_text(node, in_tail, lambda t: ref, start_pos, end_pos)

    def markup_match(self, node, match):
        """ Create a markup element for a match.

        Returns an (element, start_pos, end_pos) tuple.

        The element is the new element to insert into the tree, and the start_pos and end_pos specify
        the offsets of the chunk of text that will be replaced by the new element.
        """
        marker = etree.Element(self.marker_tag)
        marker.text = match.group(0)
        return marker, match.start(0), match.end(0)

    def ancestor_nodes(self, root):
        for x in self.ancestor_xpath(root):
            yield x

    def candidate_nodes(self, root):
        for x in self.candidate_xpath(root):
            yield x