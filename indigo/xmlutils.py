from collections import defaultdict

import lxml.html
import re
from itertools import chain

from cobalt import FrbrUri


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


html_parser = lxml.html.HTMLParser(encoding='utf-8')


def parse_html_str(html):
    """Encode HTML into utf-8 bytes and parse."""
    return lxml.html.fromstring(html.encode('utf-8'), parser=html_parser)


def rewrite_all_attachment_work_components(xml_doc):
    """ Set unique and accurate work components on all attachments.
    """
    counter = defaultdict(lambda: 0)
    ns = xml_doc.namespace
    for doc in xml_doc.root.xpath('//a:attachment/a:doc', namespaces={'a': ns}):
        parent = doc.getparent().xpath('ancestor::a:attachment/a:doc/a:meta/a:identification/a:FRBRWork/a:FRBRthis', namespaces={'a': ns})
        prefix = FrbrUri.parse(parent[-1].attrib['value']).work_component + '/' if parent else ''
        name = doc.attrib['name']
        # e.g. schedule, schedule_1/schedule, schedule_2/appendix, etc.
        prefix_name = f'{prefix}{name}'
        counter[prefix_name] += 1
        # e.g. schedule_1/schedule_3, schedule_2/appendix_1, etc.
        work_component = f'{prefix_name}_{counter[prefix_name]}'

        for part in ['a:FRBRWork', 'a:FRBRExpression', 'a:FRBRManifestation']:
            for element in doc.xpath('./a:meta/a:identification/' + part + '/a:FRBRthis', namespaces={'a': ns}):
                frbr_uri = FrbrUri.parse(element.attrib['value'])
                frbr_uri.work_component = work_component
                element.attrib['value'] = {
                    'a:FRBRWork': lambda: frbr_uri.work_uri(),
                    'a:FRBRExpression': lambda: frbr_uri.expression_uri(),
                    'a:FRBRManifestation': lambda: frbr_uri.manifestation_uri(),
                }[part]()
