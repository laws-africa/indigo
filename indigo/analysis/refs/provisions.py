import dataclasses
import re
from dataclasses import dataclass
from typing import List, Union, Tuple, Optional
import logging
from collections import deque

from lxml import etree
from lxml.etree import Element

from cobalt import FrbrUri
from docpipe.matchers import CitationMatcher, ExtractedCitation
from docpipe.xmlutils import wrap_text
from indigo.analysis.matchers import DocumentPatternMatcherMixin
from indigo.plugins import plugins
from cobalt.schemas import AkomaNtoso30
from indigo.analysis.refs.provision_refs import ParseError, Parser, TreeNode
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

    def as_dict(self):
        return dataclasses.asdict(self)


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


def parse_provision_refs(text, lang_code='eng'):
    class CustomParser(Parser):
        """This is a custom parser that overrides the method that reads the tail of the text.
        The parent parser's implementation reads character by character and creates a new TreeNode for each character.
        We don't ever use this part of the parsed text, and it matches .* (i.e. anything), so in this implementation
        we simply return a single TreeNode for the entire tail, which is much faster.

        On a test input, this reduced parse time from 1.5sec to 0.003 sec!
        """

        # supported languages
        lang_codes = ['eng', 'afr', 'fra']

        def __init__(self, lang_code, *args, **kwargs):
            if lang_code not in self.lang_codes:
                log.warning(f"Unsupported language code: {lang_code}, using 'eng' instead")
                lang_code = 'eng'
            self.lang_code = lang_code
            super().__init__(*args, **kwargs)
            self.patch_i18n()

        def patch_i18n(self):
            # find all _read_foo__i18n methods and patch them to call _read_foo__<lang_code> instead
            for name in dir(self):
                if name.startswith('_read_') and name.endswith('__i18n'):
                    lang_name = name[:-5] + self.lang_code
                    if hasattr(self, lang_name):
                        log.debug(f"Patching {name} to {lang_name}")
                        setattr(self, name, getattr(self, lang_name))
                    else:
                        raise ValueError(f"Missing translated rule {lang_name} for {name}")

        def _read_tail(self):
            node = TreeNode(self._input[self._offset:self._input_size], self._offset, [])
            self._offset = self._input_size
            return node

    class Actions:
        def root(self, input, start, end, elements):
            refs = elements[0]
            for main_refs in elements[1].elements:
                refs.extend(main_refs.references)
            target = elements[2] if not hasattr(elements[2], 'elements') else None
            return ParseResult(refs, target, elements[3].offset)

        def attachment_num_ref(self, input, start, end, elements):
            headings = {
                "schedules": "Schedule",
                "schedule": "Schedule",
                "bylae": "Bylaag",
                "bylaag": "Bylaag",
                "annexe": "Annexe",
                "annexes": "Annexe",
            }

            # extend the ref to cover the full thing, not just the number
            ref = elements[2]
            refs = [MainProvisionRef("attachment", ref)]
            # "2" -> "Schedule 2"
            heading = headings[elements[0].text.lower()]
            ref.start_pos = start
            ref.text = f'{heading} {ref.text}'

            for el in elements[3].elements or []:
                ref = MainProvisionRef("attachment", el.main_num)
                # "2" -> "Schedule 2"
                ref.ref.text = f'{heading} {ref.ref.text}'
                ref.ref.separator = el.elements[0]
                refs.append(ref)

            return refs

        def the_attachment_ref(self, input, start, end, elements):
            text = input[start:end]
            if ' ' in text:
                # assume the first word is the definite article, and skip it
                posn = text.index(' ')
                text = text[posn + 1:]
                start = start + posn + 1
            ref = ProvisionRef(text, start, end)
            return [MainProvisionRef("attachment", ref)]

        def unit_refs(self, input, start, end, elements):
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

    parser = CustomParser(lang_code, text, Actions(), None)
    return parser.parse()


class ProvisionRefsResolver:
    """Resolves references such as Section 32(a) to eIds in an Akoma Ntoso document."""

    # These are the keywords that can be matched in the text, and their corresponding element names to search for.
    # If these items change, then the grammar must be updated to match them
    # (see 'translated terminals' in provision_refs.peg)
    #
    # These also act as the basis of the pattern to look for potential references in the text to which the grammar
    # must be applied.
    element_names = {
        # all languages
        "attachment": "attachment",
        # en
        "article": "article",
        "articles": "article",
        "chapter": "chapter",
        "chapters": "chapter",
        "item": "item",
        "items": "item",
        "paragraph":    ["paragraph", "subparagraph", "item", "subsection"],
        "paragraphs":   ["paragraph", "subparagraph", "item", "subsection"],
        "part": "part",
        "parts": "part",
        "point": "point",
        "points": "point",
        "regulation": "section",
        "regulations": "section",
        "section": "section",
        "sections": "section",
        "schedule": "attachment",
        "schedules": "attachment",
        "subparagraph":     ["subparagraph", "paragraph", "item"],
        "subparagraphs":    ["subparagraph", "paragraph", "item"],
        "sub-paragraph":    ["subparagraph", "paragraph", "item"],
        "sub-paragraphs":   ["subparagraph", "paragraph", "item"],
        "sub paragraph":    ["subparagraph", "paragraph", "item"],
        "sub paragraphs":   ["subparagraph", "paragraph", "item"],
        "subregulation":    ["subsection", "paragraph", "subparagraph"],
        "subregulations":   ["subsection", "paragraph", "subparagraph"],
        "sub-regulation":   ["subsection", "paragraph", "subparagraph"],
        "sub-regulations":  ["subsection", "paragraph", "subparagraph"],
        "sub regulation":   ["subsection", "paragraph", "subparagraph"],
        "sub regulations":  ["subsection", "paragraph", "subparagraph"],
        "subsection": "subsection",
        "subsections": "subsection",
        "sub-section": "subsection",
        "sub-sections": "subsection",
        "sub section": "subsection",
        "sub sections": "subsection",
        # af
        "artikel":  ["article", "section"],
        "artikels": ["article", "section"],
        "bylaag": "attachment",
        "bylae": "attachment",
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

    # hier elements to look for when we don't have further guidance
    # we add item here because that is often used in the definitions section
    hier_elements = AkomaNtoso30.hier_elements + ['item']

    # don't look outside of these elements when resolving references to minor_hier_elements
    # that aren't otherwise scoped.
    # ref: https://github.com/laws-africa/indigo-lawsafrica/issues/1067
    major_hier_elements = [
        "article",
        "book",
        "chapter",
        "division",
        "part",
        "rule",
        "section",
        "title",
        "tome",
    ]
    minor_hier_elements = list(set(hier_elements) - set(major_hier_elements))

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
        not_outside_of = self.major_hier_elements if any(x in self.minor_hier_elements for x in names) else []
        ref.element = self.find_numbered_hier_element(local_root, names, ref.text, not_outside_of)

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

    def find_numbered_hier_element(self, root: Element, names: Optional[List[str]], num: str, not_outside_of: Optional[List[str]]=None) -> Element:
        """Find an heir element with the given number. Looks for elements with the given names, or any hier element
        if names is None. If not_outside_of is not None, then we'll look above the root element, but not go outside of
        the elements in not_outside_of (if any).
        """
        names = names or self.hier_elements
        ns = root.nsmap.get(None)
        if not ns:
            # it's not an Akoma Ntoso document, so we can't do anything
            return None

        # handle attachment differently, by looking up on the full heading
        if 'attachment' in names:
            return self.find_attachment(root, num)

        # prefix with namespace
        names = [f'{{{ns}}}{n}' for n in names]
        dead_ends = [f'{{{ns}}}{n}' for n in ['quotedStructure', 'embeddedStructure', 'content']]
        not_outside_of = None if not_outside_of is None else [f'{{{ns}}}{n}' for n in not_outside_of]

        clean_num = self.clean_num(num)

        # do a breadth-first search, starting at root, and walk upwards, expanding until we find something or reach the top
        for elem in bfs_upward_search(root, names, dead_ends, not_outside_of):
            # ignore matches to the root element, which avoids things like section (1)(a)(a) matching the same (a) twice
            if elem == root:
                continue
            num_elem = elem.find('a:num', {'a': ns})
            if num_elem is not None and self.clean_num(num_elem.text) == clean_num:
                return elem

    def clean_num(self, num):
        return num.strip("()").rstrip(".º")

    def find_attachment(self, root: Element, heading: str):
        """Find a named attachment. The whole document is searched, not just below root."""
        ns = root.nsmap.get(None)
        for heading_el in root.xpath('//a:attachment/a:heading', namespaces={'a': ns}):
            heading_text = ''.join(heading_el.itertext())
            if heading_text == heading:
                return heading_el.getparent()


class ProvisionRefsMatcher(CitationMatcher):
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
    xml_candidate_xpath = (".//text()[not("
                           "ancestor::ns:ref or ancestor::ns:heading or ancestor::ns:subheading or ancestor::ns:num "
                           "or ancestor::ns:embeddedStructure or ancestor::ns:quotedStructure or ancestor::ns:table "
                           "or ancestor::ns:crossHeading)]")

    # this just finds the start of a potential match, the grammar looks for the rest
    pattern_names = '|'.join(ProvisionRefsResolver.element_names.keys())
    the_schedule_patterns = '|'.join(['the schedule', 'die bylaag'])
    pattern_re = re.compile(fr'\b(({pattern_names})\s+([IVXLCDM0-9]|\([a-z0-9]))|({the_schedule_patterns})', re.IGNORECASE)

    resolver = ProvisionRefsResolver()
    target_root_cache = None
    document_queryset = None
    max_ref_to_target = 75

    def setup(self, *args, **kwargs):
        from indigo_api.models import Document
        super().setup(*args, **kwargs)
        self.document_queryset = Document.objects.undeleted().published()
        self.matches = []

    def run_text_extraction(self, text):
        # We override this method so that once we've found one match in a page of text, we stop looking,
        # because parse_all_refs will find all the matches in the text from the first match onwards.
        # Otherwise we end up with duplicate matches.
        for match in self.find_text_matches(text):
            if self.is_text_match_valid(text, match):
                self.handle_text_match(text, match)
                break

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
                log.debug(f"Failed to parse refs for: {s}", exc_info=e)

        # store matches for debugging purposes
        for _, pr in parses:
            if pr:
                self.matches.extend(m.ref for m in pr.references)

        return parses

    def parse_refs(self, text: str) -> ParseResult:
        return parse_provision_refs(text, self.frbr_uri.language)

    def handle_node_match(self, node, match, in_tail):
        """Process a potential citation match in the text (or tail) of a node.

        This is the main entry point for this subclass for node-based matches.

        :return: Element the rightmost newly marked up node, to continue matching in that node's tail
        """
        # There is at least one match in this node's text (or tail). If there are multiple, we must resolve them
        # from right to left, to ensure that relative provisions are linked correctly. So, we find all non-overlapping
        # full matches (using the grammar) and process them from right to left.
        parses = self.parse_all_refs(match)
        result = None
        for m, details in reversed(parses):
            res = self.handle_node_parse_result(m, details, node, in_tail)
            if result is None and res is not None:
                result = res
        return result

    def handle_text_match(self, text, match):
        """Process a potential citation match in the text of a plain-text document.

        This is the main entry point for this subclass for text-based matches.
        """
        parses = self.parse_all_refs(match)
        for m, details in reversed(parses):
            self.handle_text_parse_result(m, details)

    def handle_node_parse_result(self, match, parse_result: ParseResult, node, in_tail) -> Union[Element, None]:
        """Handle a single fully-parse match in the text (or tail) of a node.

        :return: Element the rightmost newly marked up node, to continue matching in that node's tail
        """
        # work out if the target document is this one, or another one
        target_frbr_uri, target_root = self.get_target_from_node(node, match, in_tail, parse_result)
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
        """Markup a single provision reference by wrapping it in a new market_tag node."""
        eId, last_ref = self.get_ref_eId(ref)

        # markup text[start:ref.end_pos] with ref.eId
        if eId:
            start = offset + start
            end = offset + last_ref.end_pos
            marker = etree.Element(self.marker_tag)
            marker.text = node.tail[start:end] if in_tail else node.text[start:end]
            marker.set('href', href + eId)
            wrap_text(node, in_tail, lambda t: marker, start, end)
            return marker

    def handle_text_parse_result(self, match: re.Match, parse_result: ParseResult):
        """Record a single fully-parse reference in a plain text document."""
        # work out if the target document is this one, or another one
        target_frbr_uri, target_root = self.get_target_from_text(match, parse_result.target)
        if target_root is None:
            # no target, so we can't do anything
            return None

        # resolve references into eIds
        for ref in parse_result.references:
            self.resolver.resolve_references(ref, target_root)

        href = '#' if not target_frbr_uri else f'{target_frbr_uri}/~'
        offset = match.start()

        for main_ref in parse_result.references:
            for ref in [main_ref.ref] + (main_ref.sub_refs or []):
                eId, last_ref = self.get_ref_eId(ref)
                if eId:
                    self.citations.append(
                        ExtractedCitation(
                            match.string[offset + ref.start_pos:offset + last_ref.end_pos],
                            offset + ref.start_pos,
                            offset + last_ref.end_pos,
                            href + eId,
                            self.pagenum,
                            # prefix
                            match.string[max(offset + ref.start_pos - self.text_prefix_length, 0):offset + ref.start_pos],
                            # suffix
                            match.string[offset + last_ref.end_pos:min(offset + last_ref.end_pos + self.text_suffix_length, len(match.string))],
                        )
                    )

    def get_ref_eId(self, ref: ProvisionRef):
        """Get the eId to use for this ref, and the (sub)-ref that it belongs to."""
        eId = ref.eId
        last = ref
        if ref.child:
            # get the eId of the last descendant that has one
            curr = ref.child
            while curr and curr.eId:
                eId = curr.eId
                last = curr
                curr = curr.child
        return eId, last

    def get_target_from_node(self, node: Element, match: re.Match, in_tail: bool, parse_result: ParseResult) -> (Union[str, None], Union[Element, None]):
        """Work out if the target document is this one, or a remote one, and return the target_frbr_uri and the
        appropriate root XML element of the document to use to resolve the references. If the target element
        is local to the current node, the returned target_frbr_uri is None.

        Remote targets look something like:

        - section 26(a) and (c) of Act 5 of 2009, ...
        - considering Act 5 of 2009 and section 26(a) thereof, ...
        """
        if not parse_result.target or parse_result.target == "this":
            # refs are to the local node, and we may look above that if necessary
            return None, node

        if parse_result.target == "the_act":
            # assume this is subleg and this refers to the parent work
            return self.find_parent_document_target()

        def candidates():
            # this yields candidate notes to look at, either forwards or backwards, until the first useful one is found
            # or we run out
            chars_from_ref = 0
            if parse_result.target == "thereof":
                # look backwards
                if in_tail:
                    text = node.tail
                    # eg. <p>Considering <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26 thereof, ...</p>
                    prev = node
                else:
                    # eg. <p>Considering <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <b>section 26</b> thereof, ...</p>
                    text = node.text
                    prev = node.getprevious()

                # don't cross a sentence boundary or look too far
                text = text[:match.start()]
                chars_from_ref += len(text)
                if '. ' in text or chars_from_ref > self.max_ref_to_target:
                    return

                while prev is not None:
                    # don't cross a sentence boundary or look too far: tail
                    text = prev.tail or ''
                    chars_from_ref += len(text)
                    if '. ' in text or chars_from_ref > self.max_ref_to_target:
                        return

                    yield prev

                    # don't cross a sentence boundary or look too far: text of the node we just yielded
                    text = ''.join(prev.itertext())
                    chars_from_ref += len(text)
                    # don't cross a sentence boundary or look too far
                    if '. ' in text or chars_from_ref > self.max_ref_to_target:
                        return
                    prev = prev.getprevious()
            else:
                # it's 'of', look forwards
                if in_tail:
                    # eg. <p>The term <term>dog</term> from section 26 of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>, ...</p>
                    text = node.tail
                    nxt = node.getnext()
                else:
                    # eg. <p>See section 26 of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>, ...</p>
                    text = node.text
                    nxt = next(node.iterchildren(), None)

                text = text[parse_result.end:]
                chars_from_ref += len(text)
                # don't cross a sentence boundary or look too far
                if '. ' in text or chars_from_ref > self.max_ref_to_target:
                    return

                while nxt is not None:
                    yield nxt
                    text = ''.join(nxt.itertext()) + (nxt.tail or '')
                    chars_from_ref += len(text)
                    # don't cross a sentence boundary or look too far
                    if '. ' in text or chars_from_ref > self.max_ref_to_target:
                        return
                    nxt = nxt.getnext()

        for el in candidates():
            # look for the first marker tag (usually <ref>) or <term>
            if el.tag == self.marker_tag and el.get('href'):
                return self.resolve_target_uri(node, el.get('href'))
            elif self.ns and el.tag == "{%s}%s" % (self.ns, "term") and el.get('refersTo'):
                return self.resolve_target_uri(node, el.get('refersTo'))

        return None, None

    def get_target_from_text(self, match: re.Match, target: Union[str, None]) -> (Union[str, None], Union[Element, None]):
        """Determine and resolve a remote target and return the target_frbr_uri and the appropriate root XML element of
        the document to use to resolve the references. References to the local document are not supported because
        the local document is assumed to be plain text.
        """
        if not target or target == "this":
            return None, None

        # only consider citations on this page
        # TODO: we could also look at citations in previous or later pages, and ignore offsets
        citations = [c for c in self.citations if c.target_id == self.pagenum]
        # sort by start position, then end position
        citations.sort(key=lambda c: (c.start, c.end))

        frbr_uri = None
        if target == "thereof":
            # look backwards - find the first citation before the start of this match
            for c in reversed(citations):
                if c.end < match.start():
                    # don't cross the end of a sentence or look too far behind
                    if not ('. ' in match.string[c.end:match.start()] or match.start() - c.end > self.max_ref_to_target):
                        frbr_uri = c.href
                    break

        elif target == "of":
            # it's 'of', look forwards
            # find the first citation after the end of this match, but don't cross the end of a sentence or look too far.
            for c in citations:
                if c.start > match.end():
                    # don't cross the end of a sentence or look too far ahead
                    if not ('. ' in match.string[match.end():c.start] or c.start - match.end() > self.max_ref_to_target):
                        frbr_uri = c.href
                    break

        if frbr_uri:
            return self.resolve_target_uri(None, frbr_uri)

        return None, None

    def resolve_target_uri(self, node: Element, frbr_uri: str) -> Tuple[Union[str, None], Union[Element, None]]:
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
                # only try to look locally if we have a node and it has a namespace (it's XML)
                if node is not None and node.nsmap.get(None):
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
                                    self.target_root_cache[frbr_uri] = self.resolve_target_uri(None, elements[0].get('href'))
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


@plugins.register('internal-refs')
class ProvisionRefsFinderENG(DocumentPatternMatcherMixin, ProvisionRefsMatcher):
    # country, language, locality
    locale = (None, 'eng', None)


@plugins.register('internal-refs')
class ProvisionRefsFinderAFR(DocumentPatternMatcherMixin, ProvisionRefsMatcher):
    # country, language, locality
    locale = (None, 'afr', None)


def bfs_upward_search(root, names, dead_ends, not_outside_of):
    """ Do a breadth-first search for tag_name elements, starting at root and not descending into elements named in
    dead_ends. If nothing matches, go up to the parent node (if not_outside_of is not None) and search from there. """
    # keep track of nodes we have seen, so we don't search back down into a node when we're going up a level
    visited = set()
    # the frontier is the set of nodes that we need to check
    frontier = deque([root])
    # don't search down inside these elements
    dead_ends = set(dead_ends)
    # don't go up outside of these elements
    if not_outside_of is not None:
        not_outside_of = set(not_outside_of)

    while frontier:
        node = frontier.popleft()
        visited.add(node)

        if node.tag in names:
            yield node

        # Add children to frontier
        frontier.extend(child for child in node.iterchildren() if child not in visited and child.tag not in dead_ends)

        # If queue is empty (i.e., leaf node), move upwards
        parent = node.getparent()
        if not frontier and parent is not None and not_outside_of is not None and node.tag not in not_outside_of:
            frontier.append(parent)
