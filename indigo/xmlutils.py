from __future__ import unicode_literals

import re
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
    x = wrapper(elem.tail)
    elem.tail = None
    elem.addnext(x)


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
