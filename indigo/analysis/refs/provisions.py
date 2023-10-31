import re
from dataclasses import dataclass
from typing import List, Union, Tuple
import logging
from collections import deque

from lxml import etree
from lxml.etree import Element

from cobalt import FrbrUri
from docpipe.matchers import TextPatternMatcher
from docpipe.xmlutils import wrap_text
from indigo.plugins import LocaleBasedMatcher, plugins
from cobalt.schemas import AkomaNtoso30
from indigo.analysis.refs.provision_refs import parse, ParseError
from indigo.xmlutils import closest

log = logging.getLogger(__name__)


@dataclass
class ProvisionRef:
    """A single provision reference.

    For "Section 32(a)(i) and (b)", this represents "(a)(i)".
    """
    # text of the matched reference
    text: str
    # start and end positions of the matched reference
    start_pos: int
    end_pos: int
    # "and_or", "range"
    separator: Union[str, None] = None
    # the next ref in the chain, eg "(i)" for "(a)(i)"
    child: 'ProvisionRef' = None
    element: Union[Element, None] = None
    # eId of the matched element
    eId: Union[str, None] = None


@dataclass
class MainProvisionRef:
    """The root of a series of references.

    For "Section 32(a) and (b)", this represents "Section 32(a)".
    - name: Section
    - ref: ProvisionRef("32", ..., ProvisionRef("(a)", ...))
    - sub_refs: ProvisionRef("(b)", ...)
    """
    # eg "section" or "part"
    name: str
    # the primary ref
    ref: ProvisionRef
    # secondary refs that are resolved relative to the primary
    sub_refs: List[ProvisionRef] = None


@dataclass
class ParseResult:
    references: List[MainProvisionRef]
    target: str
    # end is the offset of the meaningful text that was parsed, up to the end of the target or the last reference
    end: int


def parse_provision_refs(text):
    class Actions:
        def root(self, input, start, end, elements):
            refs = elements[0]
            for main_refs in elements[1].elements:
                refs.extend(main_refs.references)
            target = elements[2] if not hasattr(elements[2], 'elements') else None
            return ParseResult(refs, target, elements[3].offset)

        def references(self, input, start, end, elements):
            refs = [elements[2]]
            refs.extend(e.main_ref for e in elements[3].elements)
            for r in refs:
                r.name = elements[0].text
            return refs

        def main_ref(self, input, start, end, elements):
            ref = elements[0]
            sub_refs = elements[1].sub_refs if elements[1].elements else None
            if sub_refs:
                ref.child = sub_refs[0]
                sub_refs = sub_refs[1:]
            return MainProvisionRef("", ref, sub_refs or None)

        def main_num(self, input, start, end, elements):
            text = input[start:end]
            # strip right trailing dots
            if text.endswith("."):
                stripped = text[:-1]
                end = end - (len(text) - len(stripped))
                text = stripped
            return ProvisionRef(text, start, end)

        def sub_refs(self, input, start, end, elements):
            refs = [elements[0]]
            for sep, ref in elements[1].elements:
                # the first sub ref is joined with "and", "to" etc.
                ref.separator = sep
                refs.append(ref)
            return refs

        def sub_ref(self, input, start, end, elements):
            first = elements[0]
            # add the rest as children
            curr = first
            for item in elements[1].elements:
                curr.child = item.num
                curr = item.num
            return first

        def num(self, input, start, end, elements):
            return ProvisionRef(input[start:end], start, end)

        def range(self, input, start, end, elements):
            return "range"

        def and_or(self, input, start, end, elements):
            return "and_or"

        def of_this(self, input, start, end, elements):
            return "this"

        def of_the_act(self, input, start, end, elements):
            return "the_act"

        def of(self, input, start, end, elements):
            return "of"

        def thereof(self, input, start, end, elements):
            return "thereof"

    return parse(text, Actions())


class ProvisionRefsResolver:
    """Resolves references such as Section 32(a) to eIds in an Akoma Ntoso document."""

    element_names = {
        # en
        "article": "article",
        "articles": "article",
        "chapter": "chapter",
        "chapters": "chapter",
        "item": "item",
        "items": "item",
        "paragraph": ["paragraph", "subparagraph", "subsection"],
        "paragraphs": ["paragraph", "subparagraph", "subsection"],
        "part": "part",
        "parts": "part",
        "point": "point",
        "points": "point",
        "regulation": "section",
        "section": "section",
        "sections": "section",
        "subparagraph": ["subparagraph", "paragraph"],
        "subparagraphs": ["subparagraph", "paragraph"],
        "sub-paragraph": ["subparagraph", "paragraph"],
        "sub-paragraphs": ["subparagraph", "paragraph"],
        "subregulation": ["subsection", "paragraph", "subparagraph"],
        "subregulations": ["subsection", "paragraph", "subparagraph"],
        "sub-regulation": ["subsection", "paragraph", "subparagraph"],
        "sub-regulations": ["subsection", "paragraph", "subparagraph"],
        "subsection": "subsection",
        "subsections": "subsection",
        "sub-section": "subsection",
        "sub-sections": "subsection",
        # af
        "artikel": ["article", "section"],
        "artikels": ["article", "section"],
        "deel": "part",
        "dele": "part",
        "hoofstuk": "chapter",
        "hoofstukke": "chapter",
        "paragraaf": "paragraph",
        "paragrawe": "paragraph",
        "punt": "point",
        "punte": "point",
        "afdeling": "section",
        "afdelings": "section",
        "subparagraaf": "subparagraph",
        "subparagrawe": "subparagraph",
        "subafdeling": "subsection",
        "subafdelings": "subsection"
    }

    def resolve_references_str(self, text: str, root: Element):
        """Parse a string into reference objects, and the resolve them to eIds in the given root element."""
        refs = parse_provision_refs(text).references
        for ref in refs:
            self.resolve_references(ref, root)
        return refs

    def resolve_references(self, main_ref: MainProvisionRef, local_root: Element):
        """Resolve a ref, including subreferences, to element eIds in an Akoma Ntoso document."""
        # when resolving a reference like "Section 32(1)(a) and (b)", everything is relative to the first reference,
        # which is "Section 32(1)(a)". So we need to resolve that to completion first. Then, "(b)" and everything
        # after that is resolved relative to the first reference.

        # resolve the main ref
        ref = main_ref.ref
        names = self.element_names[main_ref.name.lower()]
        if not isinstance(names, list):
            names = [names]
        ref.element = self.find_numbered_hier_element(local_root, names, ref.text, True)

        if ref.element is not None:
            ref.eId = ref.element.get('eId')
            # resolve the children of the main ref
            if ref.child:
                self.resolve_ref(ref.child, [ref.element])

            if main_ref.sub_refs:
                # First, we need the elements of all children in the first ref, to use as candidate root elements
                # when resolving the rest of the refs. This means, in the example above, that "(b)" is resolved
                # against "32(1)", then "32", until successful.
                r = ref
                roots = []
                while r and r.element is not None:
                    roots.append(r.element)
                    r = r.child
                if len(roots) > 1:
                    # discard the last element, because we want to resolve "(b)" against "32(1)" not "32(1)(a)"
                    roots = roots[:-1]

                for kid in main_ref.sub_refs:
                    self.resolve_ref(kid, roots)

    def resolve_ref(self, ref, roots, names=None):
        while ref.element is None and roots:
            ref.element = self.find_numbered_hier_element(roots[-1], names, ref.text)
            if ref.element is None:
                # no match, try again with a higher root
                roots.pop(-1)

        if ref.element is not None:
            ref.eId = ref.element.get('eId')
            if ref.child:
                self.resolve_ref(ref.child, [ref.element])

    def find_numbered_hier_element(self, root: Element, names: Union[List[str], None], num: str, above_root: bool = False) -> Element:
        """Find an heir element with the given number. Looks for elements with the given names, or any hier element
        if names is None. If above_root is True, then we'll look above the root element if nothing inside matches.
        """
        names = names or AkomaNtoso30.hier_elements
        ns = root.nsmap[None]

        # prefix with namespace
        names = [f'{{{ns}}}{n}' for n in names]
        dead_ends = [f'{{{ns}}}{n}' for n in ['quotedStructure', 'embeddedStructure', 'content']]

        # do a breadth-first search, starting at root, and walk upwards, expanding until we find something or reach the top
        for elem in bfs_upward_search(root, names, dead_ends, above_root):
            # ignore matches to the root element, which avoids things like section (1)(a)(a) matching the same (a) twice
            if elem == root:
                continue
            num_elem = elem.find('a:num', {'a': ns})
            if num_elem is not None and num_elem.text.rstrip(".") == num:
                return elem


class ProvisionRefsMatcher(TextPatternMatcher):
    """ Finds internal references to sections in documents, of the form:

        # singletons
        section 26
        section 26B

        # lists
        sections 22 and 32
        and sections 19, 22 and 23, unless it appears to him
        and sections 19, 22, and 23 (oxford comma)
        and sections 19,22 and 23 (incorrect spacing)
        Sections 24, 26, 28, 36, 42(2), 46, 48, 49(2), 52, 53, 54 and 56 shall mutatis mutandis
        sections 23, 24, 25, 26 and 28;
        sections 22(1) and 25(3)(b);
        sections 18, 61 and 62(1).
        in terms of section 2 or 7
        A person who contravenes sections 4(1) and (2), 6(3), 10(1) and (2), 11(1), 12(1), 19(1), 19(3), 20(1), 20(2), 21(1), 22(1), 24(1), 25(3), (4) , (5) and (6) , 26(1), (2), (3) and (5), 28(1), (2) and (3) is guilty of an offence.
    """
    xml_marker_tag = "ref"
    xml_ancestor_xpath = '|'.join(f'//ns:{x}'
                                  for x in ['coverpage', 'preface', 'preamble', 'body', 'mainBody', 'judgmentBody', 'conclusions'])
    xml_candidate_xpath = (".//text()[not("
                           "ancestor::ns:ref or ancestor::ns:heading or ancestor::ns:subheading or ancestor::ns:num "
                           "or ancestor::ns:embeddedStructure or ancestor::ns:quotedStructure or ancestor::ns:table)]")

    # this just finds the start of a potential match, the grammar looks for the rest
    pattern_names = '|'.join(ProvisionRefsResolver.element_names.keys())
    pattern_re = re.compile(fr'\b({pattern_names})\s+(\d|\([a-z0-9])', re.IGNORECASE)

    resolver = ProvisionRefsResolver()
    target_root_cache = None
    document_queryset = None

    def setup(self, *args, **kwargs):
        from indigo_api.models import Document
        super().setup(*args, **kwargs)
        self.document_queryset = Document.objects.undeleted()

    def handle_node_match(self, node, match, in_tail):
        # There is at least one match in this node's text (or tail). If there are multiple, we must resolve them
        # from right to left, to ensure that relative provisions are linked correctly. So, we find all non-overlapping
        # full matches (using the grammar) and process them from right to left.
        parses = self.parse_all_refs(match)
        result = None
        for m, details in reversed(parses):
            res = self.handle_node_refs(m, details, node, in_tail)
            if result is None and res is not None:
                result = res
        return result

    def handle_node_refs(self, match, parse_result: ParseResult, node, in_tail) -> Union[Element, None]:
        # work out if the target document is this one, or another one
        target_frbr_uri, target_root = self.get_target(node, match, in_tail, parse_result.target)
        if target_root is None:
            # no target, so we can't do anything
            return None

        # resolve references into eIds
        for ref in parse_result.references:
            self.resolver.resolve_references(ref, target_root)

        # match is relative to the start of the text in node, but the groups are relative to the start of the match
        offset = match.start()
        href = '#' if not target_frbr_uri else f'{target_frbr_uri}/~'

        # markup from right to left so that match offsets don't change
        markers = []
        for main_ref in reversed(parse_result.references):
            # if there are sub_refs, eg "Section 32(a)(i), (b)" mark them up right to left
            if main_ref.sub_refs:
                for ref in reversed(main_ref.sub_refs):
                    marker = self.markup_ref(ref, href, ref.start_pos, offset, node, in_tail)
                    if marker is not None:
                        markers.append(marker)

            # mark up the main ref last
            ref = main_ref.ref
            marker = self.markup_ref(ref, href, ref.start_pos, offset, node, in_tail)
            if marker is not None:
                markers.append(marker)

        # return rightmost marker
        return next((m for m in markers if m is not None), None)

    def markup_ref(self, ref: ProvisionRef, href: str, start: int, offset: int, node: Element, in_tail: bool):
        eId = ref.eId
        last = ref
        if ref.child:
            # get the eId of the last descendant that has one
            curr = ref.child
            while curr and curr.eId:
                eId = curr.eId
                last = curr
                curr = curr.child

        # markup text[start:ref.end_pos] with ref.eId
        if eId:
            start = offset + start
            end = offset + last.end_pos
            marker = etree.Element(self.marker_tag)
            marker.text = node.tail[start:end] if in_tail else node.text[start:end]
            marker.set('href', href + eId)
            wrap_text(node, in_tail, lambda t: marker, start, end)
            return marker

    def parse_all_refs(self, match) -> List[Tuple[re.Match, ParseResult]]:
        """Find all the starting points and use the grammar to find non-overlapping references."""
        parses = []
        candidates = list(self.pattern_re.finditer(match.string))
        for candidate in candidates:
            # we want non-overlapping matches, so skip this candidate if it overlaps with the previous one
            if parses:
                prev_start = parses[-1][0].start()
                prev_end = prev_start + parses[-1][1].end
                if prev_start <= candidate.start() < prev_end:
                    continue

            s = match.string[candidate.start():]
            try:
                # parse the text into a list of refs using our grammar
                parses.append((candidate, self.parse_refs(s)))
            except ParseError as e:
                log.info(f"Failed to parse refs for: {s}", exc_info=e)

        return parses

    def parse_refs(self, text: str) -> ParseResult:
        return parse_provision_refs(text)

    def get_target(self, node: Element, match: re.Match, in_tail: bool, target: Union[str, None]) -> (Union[str, None], Union[Element, None]):
        """Work out if the target document is this one, or a remote one, and return the target_frbr_uri and the
        appropriate root XML element of the document to use to resolve the references. If the target element
        is local to the current node, the returned target_frbr_uri is None.

        Remote targets look something like:

        - section 26(a) and (c) of Act 5 of 2009, ...
        - considering Act 5 of 2009 and section 26(a) thereof, ...
        """
        if not target or target == "this":
            # refs are to the local node, and we may look above that if necessary
            return None, node

        if target == "the_act":
            # assume this is subleg and this refers to the parent work
            return self.find_parent_document_target()

        def candidates():
            # this yields candidate notes to look at, either forwards or backwards, until the first useful one is found
            # or we run out
            if target == "thereof":
                # look backwards
                if in_tail:
                    # eg. <p>Considering <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26 thereof, ...</p>
                    prev = node
                else:
                    # eg. <p>Considering <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <b>section 26</b> thereof, ...</p>
                    prev = node.getprevious()
                while prev is not None:
                    yield prev
                    prev = prev.getprevious()
            else:
                # it's 'of', look forwards
                if in_tail:
                    # eg. <p>The term <term>dog</term> from section 26 of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>, ...</p>
                    nxt = node.getnext()
                else:
                    # eg. <p>See section 26 of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>, ...</p>
                    nxt = next(node.iterchildren(), None)
                while nxt is not None:
                    yield nxt
                    nxt = nxt.getnext()

        for el in candidates():
            # look for the first marker tag (usually <ref>) or <term>
            if el.tag == self.marker_tag and el.get('href'):
                return self.resolve_target(node, el.get('href'))
            elif self.ns and el.tag == "{%s}%s" % (self.ns, "term") and el.get('refersTo'):
                return self.resolve_target(node, el.get('refersTo'))

        return None, None

    def resolve_target(self, node: Element, frbr_uri: str) -> Tuple[Union[str, None], Union[Element, None]]:
        """Return the target FRBR URI (if not local) and an appropriate root element for the given frbr_uri.

        The frbr_uri may be a local one (eg. "#sec_2") or it may be a full FRBR URI.
        """
        if self.target_root_cache is None:
            # this must be initialised here otherwise we have no way to override it when testing
            self.target_root_cache = {}

        if frbr_uri not in self.target_root_cache:
            # set default
            self.target_root_cache[frbr_uri] = (None, None)

            # is the URI a local one?
            if frbr_uri.startswith('#'):
                if frbr_uri.startswith('#term-'):
                    # look for a ref in the definition of the term
                    elements = node.xpath(f'//a:def[@refersTo="{frbr_uri}"]', namespaces={'a': node.nsmap[None]})
                    if elements:
                        # find the element that wraps the definition
                        defn = closest(elements[0].getparent(), lambda e: e.get('refersTo', '') == frbr_uri)
                        if defn is not None:
                            # find the first absolute ref in the definition
                            elements = defn.xpath('.//a:ref[starts-with(@href, "/akn")]', namespaces={'a': node.nsmap[None]})
                            if elements:
                                self.target_root_cache[frbr_uri] = self.resolve_target(None, elements[0].get('href'))
                else:
                    elements = node.xpath(f'//a:*[@eId="{frbr_uri[1:]}"]', namespaces={'a': node.nsmap[None]})
                    if elements:
                        self.target_root_cache[frbr_uri] = (None, elements[0])
            else:
                try:
                    # we normalise the FRBR URI to the work level
                    uri = FrbrUri.parse(frbr_uri)
                    self.target_root_cache[frbr_uri] = (frbr_uri, self.find_document_root(uri))
                except ValueError:
                    # bad FRBR URI
                    pass

        return self.target_root_cache[frbr_uri]

    def find_document_root(self, frbr_uri: FrbrUri) -> Union[Element, None]:
        doc = self.document_queryset.filter(work__frbr_uri=frbr_uri.work_uri(False)).latest_expression().first()
        if doc:
            return doc.doc.root

    def find_parent_document_target(self) -> Union[Element, None]:
        # find a document for this frbr uri, provided it has a parent
        doc = (
            self.document_queryset
            .filter(work__frbr_uri=self.frbr_uri.work_uri(False), work__parent_work__isnull=False)
            .only('work__parent_work_id')
            .first())
        if doc:
            # now get the parent
            doc = self.document_queryset.filter(work_id=doc.work.parent_work_id).latest_expression().first()
            if doc:
                return doc.work.frbr_uri, doc.doc.root

        return None, None


class BaseProvisionRefsFinder(LocaleBasedMatcher, ProvisionRefsMatcher):
    def find_references_in_document(self, document):
        """ Find references in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content)
        self.markup_xml_matches(document.expression_uri, root)
        document.content = etree.tostring(root, encoding='unicode')


@plugins.register('internal-refs')
class ProvisionRefsFinderENG(BaseProvisionRefsFinder):
    # country, language, locality
    locale = (None, 'eng', None)


@plugins.register('internal-refs')
class ProvisionRefsFinderAFR(BaseProvisionRefsFinder):
    # country, language, locality
    locale = (None, 'afr', None)


def bfs_upward_search(root, names, dead_ends, above_root):
    """ Do a breadth-first search for tag_name elements, starting at root and not descending into elements named in
    dead_ends. If nothing matches, go up to the parent node (if above_root is True) and search from there. """
    # keep track of nodes we have seen, so we don't search back down into a node when we're going up a level
    visited = set()
    # the frontier is the set of nodes that we need to check
    frontier = deque([root])

    while frontier:
        node = frontier.popleft()
        visited.add(node)

        if node.tag in names:
            yield node

        # Add children to frontier
        frontier.extend(child for child in node.iterchildren() if child not in visited and child.tag not in dead_ends)

        # If queue is empty (i.e., leaf node), move upwards
        if not frontier and node.getparent() is not None and above_root:
            parent = node.getparent()
            frontier.append(parent)
