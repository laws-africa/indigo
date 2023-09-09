import re
from dataclasses import dataclass
from typing import List, Union

from lxml import etree
from lxml.etree import Element
from docpipe.matchers import TextPatternMatcher
from docpipe.xmlutils import wrap_text
from schemas import AkomaNtoso30


@dataclass
class ProvisionRef:
    # text of the matched reference
    text: str
    # start and end positions of the matched reference
    start_pos: int
    end_pos: int
    # eId of the matched element
    eId: str


class InternalRefsResolver:
    # TODO: expand beyond section
    prefix_re = re.compile(r'^((?P<name>section)s?)\s+(?P<num>\d+[A-Z0-9]*)', re.IGNORECASE)

    def resolve_references(self, text: str, root: Element) -> List[List[ProvisionRef]]:
        """Resolve the references in text, in the context of the provided root element. Returns a list of
        ProvisionRef lists. Each sublist describes a run of numbers that reference a single element.

        For example, "section 1(1)(a) and (b)" would return two lists, one for "section 1(1)(a)" and one for "(b)".

        It is expected that the text is for a single type of related references, such as:

        - section 26
        - sections 22 and 32
        - sections 19(a) to (c), 22, and 23(b)(1)
        """
        refs = []
        initial_ref = []
        group = []

        # check for initial prefix
        prefix = self.prefix_re.match(text)
        if prefix:
            # look it up and use it as the new root
            root = self.find_numbered_hier_element(root, [prefix['name'].lower()], prefix['num'])
            if root is None:
                return refs
            initial_ref = ProvisionRef(prefix.group(0), prefix.start(), prefix.end(), root.get('eId'))
            group.append(initial_ref)

        # Split a sequence of provision numbers into an array.
        # eg. "(a)(i)" becomes ["(a)", "(i)"]
        # TODO: handle "and" and "to"
        # TODO: handle multiple
        matches = list(re.finditer(r"\([0-9a-z]{1,3}\)", text))
        if not matches:
            # only the prefix, if any
            if group:
                refs.append(group)
            return refs

        nums = [m.group(0) for m in matches]
        elems = self.ref_nums_to_elements(nums, root)
        for match, elem in zip(matches, elems):
            if elem is None:
                # we matched as far as we could
                break
            if elem.get('eId'):
                group.append(ProvisionRef(match.group(0), match.start(0), match.end(0), elem.get('eId')))

        if group:
            refs.append(group)

        return refs

    def ref_nums_to_elements(self, nums: List[str], elem: Element) -> List[Union[Element, None]]:
        """ Return the XML elements correspond with the numbers in nums, such as "(b)(i)".
        If an item cannot be found, it and sebsequent components will be None.
        """
        path = [None] * len(nums)
        for i, num in enumerate(nums):
            elem = self.find_numbered_hier_element(elem, None, num)
            if elem is None:
                break
            path[i] = elem
        return path

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


class NewInternalRefsFinder(TextPatternMatcher):
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

        TODO: match subsections
        TODO: match paragraphs
        TODO: match ranges of sections
    """
    xml_marker_tag = "ref"
    xml_ancestor_xpath = '|'.join(f'//ns:{x}'
                                  for x in ['coverpage', 'preface', 'preamble', 'body', 'mainBody', 'judgmentBody', 'conclusions'])
    xml_candidate_xpath = ".//text()[not(ancestor::ns:ref)]"

    pattern_re = re.compile(
        r'''\b
        (
          (?P<ref>
            (?<!-)sections?\s+
            (?P<num>\d+[A-Z0-9]*)    # first section number, including subsections
          )
          (
            (\s*(,|and|or))*         # list separators
            (\s*\([A-Z0-9]+\))+      # bracketed subsections of first number
          )*
          (\s*                       # optional list of sections
            (\s*(,|and|or))*         # list separators
            (
              \s*\d+[A-Z0-9]*(
                (\s*(,|and|or))*     # list separators
                (\s*\([A-Z0-9]+\))+
              )*
            )
          )*
        )
        (\s+of\s+(this)?|\s+thereof)?
        ''',
        re.X | re.IGNORECASE)

    # TODO: bigger pattern
    # TODO: individual parts of a big pattern

    resolver = InternalRefsResolver()

    def handle_node_match(self, node, match, in_tail):
        # TODO:
        # markup all the refs in this single match, which could be multiple ones
        # we want to process from right to left, so that offsets don't change
        # finally, we must return the rightmost node, so that the matcher keeps looking at that node's tail text

        # TODO: extract the "runs"
        # TODO: process each run
        # TODO: determine the target document
        root = node.getroottree().getroot()
        # TODO: handle remote references
        is_local = True
        if is_local:
            href = '#'
        else:
            target_work_frbr_uri = ''
            href = target_work_frbr_uri + "/~"
        groups = self.resolver.resolve_references(match.group(0), root)
        first_marker = None
        # match is relative to the start of the text in node, but the groups are relative to the start of the match
        offset = match.start()

        # markup from right to left so that match offsets don't change
        for group in reversed(groups):
            # for a group that covers something like 2(a)(i), we mark up the entire string and use the eId of the
            # final element
            if group[-1].eId:
                marker = etree.Element(self.marker_tag)
                marker.text = ''.join(ref.text for ref in group)
                marker.set('href', href + group[-1].eId)
                wrap_text(node, in_tail, lambda t: marker, offset + group[0].start_pos, offset + group[-1].end_pos)
                if first_marker is None:
                    first_marker = marker

        # return the rightmost element
        return first_marker
