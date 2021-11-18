import re
from itertools import chain

import lxml.html
from lxml import etree


def fragments_fromstring(html):
    """ Same as lxml.html.fragments_fromstring, except we preserve initial whitespace.
    """
    items = lxml.html.fragments_fromstring(html)
    match = re.match(r'^(\s+)<', html)
    if match:
        items.insert(0, match.group(1))
    return items


def wrap_tail(elem, wrapper):
    """ Wrap the tail text of elem in wrapper (a callable), and
    append the new element directly after elem.
    """
    return wrap_text(elem, True, wrapper)


def wrap_text(node, tail, wrapper, start_pos=None, end_pos=None):
    """ Wrap the text (or tail if tail is True) of a node in wrapper (a callable).
    Optionally, start_pos and end_pos specify the substring of the node's text (or tail)
    to be wrapped. The wrapper callable will be called with the text being wrapped.
    """
    if tail:
        text = node.tail or ''
        start_pos = start_pos or 0
        end_pos = len(text) if end_pos is None else end_pos
        wrapped = wrapper(text[start_pos:end_pos])

        node.addnext(wrapped)
        node.tail = text[:start_pos]
        wrapped.tail = text[end_pos:]
    else:
        text = node.text or ''
        start_pos = start_pos or 0
        end_pos = len(text) if end_pos is None else end_pos
        wrapped = wrapper(text[start_pos:end_pos])

        node.text = text[:start_pos]
        node.insert(0, wrapped)
        wrapped.tail = text[end_pos:]

    return wrapped


def unwrap_element(elem):
    """ Unwrap text and children inside elem, making them children
    of elem's parents.

    Example:
        <p>text <term>a <b>term</b></term> with a tail</p>

        unwrapping <term> produces:

        <p>text a <b>term</b> with a tail</p>
    """
    parent = elem.getparent()
    prev = elem.getprevious()

    if prev is not None:
        # elem is not the first child of its parent
        prev.tail = (prev.tail or '') + (elem.text or '')
        index = parent.index(elem)
        last = None
        for child in elem.iterchildren(reversed=True):
            if last is None:
                last = child
            parent.insert(index, child)

        if last is None:
            last = prev
        last.tail = (last.tail or '') + (elem.tail or '')

    else:
        # elem is first child of its parent
        parent.text = (parent.text or '') + (elem.text or '')
        last = None
        for child in elem.iterchildren(reversed=True):
            if last is None:
                last = child
            parent.insert(0, child)

        if last is not None:
            last.tail = (last.tail or '') + (elem.tail or '')
        else:
            parent.text = (parent.text or '') + (elem.tail or '')

    parent.remove(elem)


def rewrite_ids(elem, old_id_prefix, new_id_prefix):
    mappings = {}
    old_id = elem.get('eId')
    old_id_len = len(old_id_prefix)
    if old_id and old_id.startswith(old_id_prefix):
        new_id = new_id_prefix + old_id[old_id_len:]
        mappings[old_id] = new_id
        elem.set('eId', new_id)

    # rewrite children
    for child in elem.xpath('.//a:*[@eId]', namespaces={'a': elem.nsmap[None]}):
        old_id = child.get('eId')
        if old_id.startswith(old_id_prefix):
            new_id = new_id_prefix + old_id[old_id_len:]
            mappings[old_id] = new_id
            child.set('eId', new_id)

    return mappings


def closest(element, predicate):
    """ Starting at the given element, find the closest node in the ancestor
    chain that satisfies the given lambda expression.
    """
    try:
        return next(e for e in chain([element], element.iterancestors()) if predicate(e))
    except StopIteration:
        return None


class EIdRewriter:
    """ Support class for rewriting eIds of elements in an existing XML document.
    """
    # leading whitespace and punctuation
    leading_punct_re = re.compile(r'^[\s\u2000-\u206f\u2e00-\u2e7f!"#$%&\'()*+,\-./:;<=>?@\[\]^_`{|}~]+')
    # trailing whitespace and punctuation
    trailing_punct_re = re.compile(r'[\s\u2000-\u206f\u2e00-\u2e7f!"#$%&\'()*+,\-./:;<=>?@\[\]^_`{|}~]+$')
    # whitespace
    whitespace_re = re.compile(r'\s')
    # general punctuation
    punct_re = re.compile(r'[\u2000-\u206f\u2e00-\u2e7f!"#$%&\'()*+,\-./:;<=>?@\[\]^_`{|}~]+')

    id_unnecessary = set("arguments background conclusions decision header introduction motivation preamble preface"
                         " remedies".split())
    """ Elements for which an id is optional. """

    num_expected = set("alinea article book chapter clause division indent item level list"
                       " paragraph part point proviso rule section subchapter subclause"
                       " subdivision sublist subparagraph subpart subrule subsection subtitle"
                       " title tome transitional".split())
    """ Elements for which a num is expected. """

    dont_prefix = ['section']
    """ Elements that for historical reasons aren't prefixed with their parent's eId. """

    aliases = {
        'alinea': 'al',
        'amendmentBody': 'body',
        'article': 'art',
        'attachment': 'att',
        'blockList': 'list',
        'chapter': 'chp',
        'citation': 'cit',
        'citations': 'cits',
        'clause': 'cl',
        'component': 'cmp',
        'components': 'cmpnts',
        'componentRef': 'cref',
        'debateBody': 'body',
        'debateSection': 'dbsect',
        'division': 'dvs',
        'documentRef': 'dref',
        'eventRef': 'eref',
        'judgmentBody': 'body',
        'listIntroduction': 'intro',
        'listWrapUp': 'wrapup',
        'mainBody': 'body',
        'paragraph': 'para',
        'quotedStructure': 'qstr',
        'quotedText': 'qtext',
        'recital': 'rec',
        'recitals': 'recs',
        'section': 'sec',
        'subchapter': 'subchp',
        'subclause': 'subcl',
        'subdivision': 'subdvs',
        'subparagraph': 'subpara',
        'subsection': 'subsec',
        'temporalGroup': 'tmpg',
        'wrapUp': 'wrapup',
    }

    def __init__(self, ns):
        self.counters = {}
        self.eid_counter = {}
        self.ns = ns

    def incr(self, prefix, name):
        sub = self.counters.setdefault(prefix, {})
        sub[name] = sub.get(name, 0) + 1
        return sub[name]

    def make(self, prefix, item, name):
        if name in self.dont_prefix and not prefix.startswith('att_'):
            prefix = ''

        eid = (f'{prefix}__' if prefix else '') + self.aliases.get(name, name)

        if self.needs_num(name):
            num, nn = self.get_num(item, prefix, name)
            eid = self.ensure_unique(f'{eid}_{num}', nn)

        return eid

    def get_num(self, item, prefix, name):
        num = None
        nn = False

        item_num = etree.XPath(f'./a:num', namespaces={'a': self.ns})(item)
        if item_num:
            num = self.clean_num(item_num[0].text)

        if not num and self.needs_nn(name):
            num = 'nn'
            nn = True

        # produce e.g. hcontainer_1
        if not num:
            num = self.incr(prefix, name)

        return num, nn

    def ensure_unique(self, eid, nn):
        # update counter with number of elements with this eid, including this one
        count = self.eid_counter[eid] = self.eid_counter.get(eid, 0) + 1

        # eid must be unique, and unnumbered elements must end with _{count} regardless
        if count == 1 and not nn:
            return eid

        # if it's not unique, or the element is unnumbered,
        # include the count for disambiguation and check for uniqueness
        return self.ensure_unique(f'{eid}_{count}', nn=False)

    def needs_num(self, name):
        return name not in self.id_unnecessary

    def needs_nn(self, name):
        return name in self.num_expected

    def clean_num(self, num):
        """ Clean a <num> value for use in an eId
        See https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/os/akn-nc-v1.0-os.html*_Toc531692306

        "The number part of the identifiers of such elements corresponds to the
        stripping of all final punctuation, meaningless separations as well as
        redundant characters in the content of the <num> element. The
        representation is case-sensitive."

        Our algorithm is:
        1. strip all leading and trailing whitespace and punctuation (using the unicode punctuation blocks)
        2. strip all whitespace
        3. replace all remaining punctuation with a hyphen.

        The General Punctuation block is \u2000-\u206F, and the Supplemental Punctuation block is \u2E00-\u2E7F.

        (i) -> i
        1.2. -> 1-2
        “2.3“ -> 2-3
        3a bis -> 3abis
        """
        num = self.leading_punct_re.sub('', num)
        num = self.trailing_punct_re.sub('', num)
        num = self.whitespace_re.sub('', num)
        num = self.punct_re.sub('-', num)
        return num
