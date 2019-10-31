from lxml import etree
import re

from indigo.plugins import LocaleBasedMatcher, plugins
from indigo.xmlutils import closest


class BaseRefsFinder(LocaleBasedMatcher):
    """ Finds references to Acts in documents.
    """

    act_re = None
    """ This must be defined by a subclass. It should be a compiled regular
    expression, with named captures for `ref`, `num` and `year`.
    """
    candidate_xpath = None
    """ Xpath for candidate text nodes that should be tested for references.
    Must be defined by subclasses.
    """

    # the ancestor elements that can contain references
    ancestors = ['coverpage', 'preface', 'preamble', 'body', 'mainBody', 'conclusions']

    def find_references_in_document(self, document):
        """ Find references in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content)
        self.frbr_uri = document.doc.frbr_uri
        self.setup(root)
        self.find_references(root)
        document.content = etree.tostring(root, encoding='utf-8').decode('utf-8')

    def setup(self, root):
        self.ns = root.nsmap[None]
        self.nsmap = {'a': self.ns}
        self.ref_tag = "{%s}ref" % self.ns

        self.ancestor_xpath = etree.XPath('|'.join('.//a:%s' % a for a in self.ancestors), namespaces=self.nsmap)
        self.candidate_xpath = etree.XPath(self.candidate_xpath, namespaces=self.nsmap)

    def make_href(self, match):
        """ Turn this match into a full FRBR URI href
        """
        return '/%s/act/%s/%s' % (self.frbr_uri.country, match.group('year'), match.group('num'))

    def find_references(self, root):
        for root in self.ancestor_nodes(root):
            for candidate in self.candidate_nodes(root):
                node = candidate.getparent()

                if not candidate.is_tail:
                    # text directly inside a node
                    match = self.act_re.search(node.text)
                    if match:
                        # mark the reference and continue to check the new tail
                        node = self.mark_reference(node, match, in_tail=False)

                while node is not None and node.tail:
                    match = self.act_re.search(node.tail)
                    if not match:
                        break

                    # mark the reference and continue to check the new tail
                    node = self.mark_reference(node, match, in_tail=True)

    def mark_reference(self, node, match, in_tail):
        ref, start_pos, end_pos = self.make_ref(match)

        if in_tail:
            node.addnext(ref)
            node.tail = match.string[:start_pos]
            ref.tail = match.string[end_pos:]
        else:
            node.text = match.string[:start_pos]
            node.insert(0, ref)
            ref.tail = match.string[end_pos:]

        return ref

    def make_ref(self, match):
        """ Make a reference out of this match, returning a (ref, start, end) tuple
        which is the new ref node, and the start and end position of what text
        in the parent element it should be replacing.

        By default, the first group in the `act_re` is substituted with the ref.
        """
        ref = etree.Element(self.ref_tag)
        ref.text = match.group('ref')
        ref.set('href', self.make_href(match))
        return (ref, match.start('ref'), match.end('ref'))

    def ancestor_nodes(self, root):
        for x in self.ancestor_xpath(root):
            yield x

    def candidate_nodes(self, root):
        for x in self.candidate_xpath(root):
            yield x


@plugins.register('refs')
class RefsFinderENG(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Act 52 of 2001
        Act no. 52 of 1998
        Income Tax Act, 1962 (No 58 of 1962)

    """

    # country, language, locality
    locale = (None, 'eng', None)

    act_re = re.compile(
        r'''\bAct,?\s+
            (\d{4}\s+)?
            \(?
            (?P<ref>
             ([nN]o\.?\s*)?
             (?P<num>\d+)\s+
             of\s+
             (?P<year>\d{4})
            )
        ''', re.X)
    candidate_xpath = ".//text()[contains(., 'Act') and not(ancestor::a:ref)]"


class BaseInternalRefsFinder(LocaleBasedMatcher):
    """ Finds internal references in documents, such as to sections.
    """

    ref_re = None
    """ This must be defined by a subclass. It should be a compiled regular
    expression, with named captures for `ref` and `num`.
    """
    candidate_xpath = None
    """ Xpath for candidate text nodes that should be tested for references.
    Must be defined by subclasses.
    """

    # the ancestor elements that can contain references
    ancestors = ['body', 'mainBody', 'conclusions']

    def find_references_in_document(self, document):
        """ Find references in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content)
        self.setup(root)
        self.find_references(root)
        document.content = etree.tostring(root, encoding='utf-8').decode('utf-8')

    def setup(self, root):
        self.ns = root.nsmap[None]
        self.nsmap = {'a': self.ns}
        self.ref_tag = f'{{{self.ns}}}ref'
        self.ancestor_xpath = etree.XPath('|'.join(f'.//a:{a}' for a in self.ancestors), namespaces=self.nsmap)
        self.candidate_xpath = etree.XPath(self.candidate_xpath, namespaces=self.nsmap)

    def find_references(self, root):
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
        return self.ref_re.finditer(text)

    def is_valid(self, node, match):
        return self.find_target(node, match) is not None

    def handle_match(self, node, match, in_tail):
        """ Process a match. If this modifies the text (or tail, if in_tail is True), then
        return the new node that should have its tail checked for further matches.
        Otherwise, return None.
        """
        if self.is_valid(node, match):
            ref, start_pos, end_pos = self.make_ref(node, match)
            return self.mark_reference(node, ref, start_pos, end_pos, in_tail)

    def find_target(self, node, match):
        """ Return the target element that this reference targets.
        """
        raise NotImplementedError()

    def mark_reference(self, node, ref, start_pos, end_pos, in_tail):
        if in_tail:
            text = node.tail or ''
            node.addnext(ref)
            node.tail = text[:start_pos]
            ref.tail = text[end_pos:]
        else:
            text = node.text or ''
            node.text = text[:start_pos]
            node.insert(0, ref)
            ref.tail = text[end_pos:]

        return ref

    def make_ref(self, node, match):
        """ Make a reference out of this match, returning a (ref, start, end) tuple
        which is the new ref node, and the start and end position of what text
        in the parent element it should be replacing.
        """
        ref = etree.Element(self.ref_tag)
        ref.text = match.group('ref')
        ref.set('href', self.make_href(node, match))
        return ref, match.start('ref'), match.end('ref')

    def make_href(self, node, match):
        """ Return the target href for this match.
        """
        raise NotImplementedError()

    def ancestor_nodes(self, root):
        for x in self.ancestor_xpath(root):
            yield x

    def candidate_nodes(self, root):
        for x in self.candidate_xpath(root):
            yield x


@plugins.register('internal-refs')
class SectionRefsFinderENG(BaseInternalRefsFinder):
    """ Finds internal references to sections in documents, of the form:

        # singletons
        section 26
        section 26B

        # lists
        sections 22 and 32
        and sections 19, 22 and 23, unless it appears to him
        Sections 24, 26, 28, 36, 42(2), 46, 48, 49(2), 52, 53, 54 and 56 shall mutatis mutandis
        sections 23, 24, 25, 26 and 28;
        sections 22(1) and 25(3)(b);
        sections 18, 61 and 62(1).
        in terms of section 2 or 7
        sections 12(6)(d) and (e)
        Subject to sections 1(4), 3(6), 4, 8, 24, 34(2) and 44, no person

        TODO: match subsections
        TODO: match paragraphs
        TODO: match ranges of sections
    """

    # country, language, locality
    locale = (None, 'eng', None)

    ref_re = re.compile(
        r'''\b
        (
          (?P<ref>
            sections?\s+
            (?P<num>\d+[A-Z0-9]*)  # first section number, including subsections
          )
          (\s*\([A-Z0-9]+\))*      # bracketed subsections of first number
          (\s*                     # optional list of sections
            (,|and|or)\s+          # list separators
            (\d+[A-Z0-9]*(\([A-Z0-9]+\))*)
          )*
        )
        (\s+of\s+(this\s+Act|the\s+|Act\s+)?)?
        ''',
        re.X | re.IGNORECASE)

    # individual numbers in the list grouping above
    item_re = re.compile(r'(?P<ref>(?P<num>\d+[A-Z0-9]*))[A-Z0-9()]*', re.IGNORECASE)

    candidate_xpath = ".//text()[contains(translate(., 'S', 's'), 'section') and not(ancestor::a:ref)]"
    match_cache = {}

    def setup(self, root):
        super().setup(root)
        self.ancestor_tags = set(f'{{{self.ns}}}{t}' for t in self.ancestors)

    def is_valid(self, node, match):
        # check that it's not an external reference
        ref = match.group(0)
        if ref.endswith('the ') or ref.endswith('Act '):
            return False
        return True

    def handle_match(self, node, full_match, in_tail):
        # we've found a reference to (potentially) a list of section refs.
        # we handle each item in the list separately, from right to left so
        # that the match offsets don't change.
        if not self.is_valid(node, full_match):
            # keep searching
            return None

        items = list(self.item_re.finditer(full_match.group(1)))
        if len(items) == 1:
            # markup the whole of "Section 26" as a link, rather than just "26"
            items = [full_match]
            offset = 0
        else:
            offset = full_match.start(1)

        last = None
        for match in reversed(items):
            if self.is_item_valid(node, match):
                ref = self.mark_item_reference(node, match, offset, in_tail)
                if last is None:
                    last = ref

        return last

    def find_target(self, node, match):
        num = match.group('num')
        # find the closest ancestor to scope the lookups to
        ancestor = closest(node, lambda e: e.tag in self.ancestor_tags)
        candidate_elements = ancestor.xpath(f".//a:section[a:num[text()='{num}.']]", namespaces=self.nsmap)
        if candidate_elements:
            self.match_cache[num] = candidate_elements[0]
            return candidate_elements[0]

    def is_item_valid(self, node, match):
        # use the traditional validity check
        return super().is_valid(node, match)

    def mark_item_reference(self, node, match, offset, in_tail):
        ref, start_pos, end_pos = self.make_ref(node, match)
        return self.mark_reference(node, ref, start_pos + offset, end_pos + offset, in_tail)

    def make_href(self, node, match):
        target = self.match_cache[match.group('num')]
        return '#' + target.get('id')
