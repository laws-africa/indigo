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
