import re
from itertools import chain

import lxml.html


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
