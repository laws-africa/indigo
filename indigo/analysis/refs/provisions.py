import re
from dataclasses import dataclass
from typing import List, Union, Tuple

from lxml import etree
from lxml.etree import Element

from cobalt import FrbrUri
from docpipe.matchers import TextPatternMatcher
from docpipe.xmlutils import wrap_text
from indigo.plugins import LocaleBasedMatcher, plugins
from cobalt.schemas import AkomaNtoso30
from indigo.analysis.refs.provision_refs import parse, ParseError


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
        "paragraph": "paragraph",
        "paragraphs": "paragraph",
        "point": "point",
        "points": "point",
        "section": "section",
        "sections": "section",
        "subparagraph": "subparagraph",
        "subparagraphs": "subparagraph",
        "subsection": "subsection",
        "subsections": "subsection",
        # af
        "artikel": "article",
        "artikels": "article",
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
        refs = parse_provision_refs(text)["references"]
        for ref in refs:
            self.resolve_references(ref, root)
        return refs

    def resolve_references(self, main_ref: MainProvisionRef, root: Element):
        """Resolve a ref, including subreferences, to element eIds in an Akoma Ntoso document."""
        # when resolving a reference like "Section 32(1)(a) and (b)", everything is relative to the first reference,
        # which is "Section 32(1)(a)". So we need to resolve that to completion first. Then, "(b)" and everything
        # after that is resolved relative to the first reference.

        # resolve the main ref
        ref = main_ref.ref
        ref.element = self.find_numbered_hier_element(root, [self.element_names[main_ref.name.lower()]], ref.text)

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

    def find_numbered_hier_element(self, root: Element, names: Union[List[str], None], num: str) -> Element:
        """Find an heir element with the given number. Looks for elements with the given names, or any hier element
        if names is None.
        """
        names = names or AkomaNtoso30.hier_elements
        ns = {'a': root.nsmap[None]}

        # TODO: the .// isn't quite right, because we want to do a breadth-first search of hier children
        xpath = '|'.join(f'.//a:{x}' for x in names)
        for elem in root.xpath(xpath, namespaces=ns):
            num_elem = elem.find('a:num', ns)
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
                           "ancestor::ns:embeddedStructure or ancestor::ns:quotedStructure)]")

    # this just finds the start of a potential match, the grammar looks for the rest
    pattern_names = '|'.join(ProvisionRefsResolver.element_names.keys())
    pattern_re = re.compile(fr'\b({pattern_names})\s+\d', re.IGNORECASE)

    resolver = ProvisionRefsResolver()
    target_root_cache = None
    document_queryset = None

    def setup(self, *args, **kwargs):
        from indigo_api.models import Document
        super().setup(*args, **kwargs)
        self.document_queryset = Document.objects.undeleted()

    def handle_node_match(self, node, match, in_tail):
        # parse the text into a list of refs using our grammar
        try:
            main_refs, target = self.parse_refs(match.string[match.start():])
        except ParseError:
            return None

        # work out if the target document is this one, or another one
        target_frbr_uri, target_root = self.get_target(node, match, in_tail, target)
        if target_root is None:
            # no target, so we can't do anything
            return None

        # resolve references into eIds
        for ref in main_refs:
            self.resolver.resolve_references(ref, target_root)

        # match is relative to the start of the text in node, but the groups are relative to the start of the match
        offset = match.start()
        href = '#' if not target_frbr_uri else f'{target_frbr_uri}/~'

        # markup from right to left so that match offsets don't change
        markers = []
        for main_ref in reversed(main_refs):
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

    def parse_refs(self, text: str) -> Tuple[List[MainProvisionRef], any]:
        result = parse_provision_refs(text)
        return result["references"], result.get("target")

    def get_target(self, node: Element, match: re.Match, in_tail: bool, target: Union[str, None]) -> (Union[str, None], Union[Element, None]):
        """Work out if the target document is this one, or a remote one, and return the target_frbr_uri and the
        root XML element of the document to use to resolve the references.

        Remote targets look something like:

        - section 26(a) and (c) of Act 5 of 2009, ...
        - considering Act 5 of 2009 and section 26(a) thereof, ...
        """
        if not target or target == "this":
            # refs are to the local document
            return None, node.getroottree().getroot()

        if target == "thereof":
            # look backwards
            if in_tail:
                # eg. <p>Considering <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26 thereof, ...</p>
                prev = node
            else:
                # eg. <p>Considering <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <b>section 26</b> thereof, ...</p>
                prev = node.getprevious()
            while prev is not None:
                if prev.tag == self.marker_tag and prev.get('href'):
                    frbr_uri = prev.get('href')
                    return frbr_uri, self.get_target_root(frbr_uri)
                prev = prev.getprevious()
            return None, None

        # it's 'of', look forwards
        if in_tail:
            # eg. <p>The term <term>dog</term> from section 26 of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>, ...</p>
            nxt = node.getnext()
        else:
            # eg. <p>See section 26 of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>, ...</p>
            nxt = next(node.iterchildren(), None)
        while nxt is not None:
            if nxt.tag == self.marker_tag and nxt.get('href'):
                frbr_uri = nxt.get('href')
                return frbr_uri, self.get_target_root(frbr_uri)
            nxt = nxt.getnext()

        return None, None

    def get_target_root(self, frbr_uri: str) -> Union[Element, None]:
        """Return the root element of the document for the given frbr_uri."""
        # check the cache
        if self.target_root_cache is None:
            self.target_root_cache = {}
        elif frbr_uri in self.target_root_cache:
            return self.target_root_cache[frbr_uri]

        try:
            uri = FrbrUri.parse(frbr_uri)
        except ValueError:
            return None

        # we normalise the FRBR URI to the work level
        doc = self.find_document_root(uri)
        if doc:
            self.target_root_cache[frbr_uri] = root = doc.doc.root
            return root

    def find_document_root(self, frbr_uri: FrbrUri) -> Union[Element, None]:
        return self.document_queryset.filter(work__frbr_uri=frbr_uri.work_uri(False)).latest_expression().first()


class BaseProvisionRefsFinder(LocaleBasedMatcher, ProvisionRefsMatcher):
    def find_references_in_document(self, document):
        """ Find references in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content)
        self.setup(root)
        self.markup_xml_matches(document.frbr_uri, root)
        document.content = etree.tostring(root, encoding='utf-8').decode('utf-8')


@plugins.register('internal-refs')
class ProvisionRefsFinderENG(BaseProvisionRefsFinder):
    # country, language, locality
    locale = (None, 'eng', None)


@plugins.register('internal-refs')
class ProvisionRefsFinderAFR(BaseProvisionRefsFinder):
    # country, language, locality
    locale = (None, 'afr', None)


def parse_provision_refs(text):
    class Actions:
        def root(self, input, start, end, elements):
            refs = elements[0]
            for main_refs in elements[1].elements:
                refs.extend(main_refs.references)
            target = elements[2] if not hasattr(elements[2], 'elements') else None
            return {'references': refs, 'target': target}

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

        def of(self, input, start, end, elements):
            return "of"

        def thereof(self, input, start, end, elements):
            return "thereof"

    return parse(text, Actions())
