import copy
import html
from difflib import SequenceMatcher
import logging
import os
import re

import jsonpatch
import lxml.html
import lxml.html.builder
from lxml import etree
from xmldiff import formatting
from xmldiff.diff import Differ
from cobalt.schemas import AkomaNtoso30
from docpipe.xmlutils import unwrap_element

log = logging.getLogger(__name__)


class IgnoringDiffer(Differ):
    """ Ignores most data- attributes.
    """
    allowed = ['data-refersto']

    def node_attribs(self, node):
        attribs = dict(node.attrib)
        for k in list(attribs.keys()):
            if k.startswith('data-') and k not in self.allowed:
                del attribs[k]
        return attribs


class IgnoringPlaceholderMaker(formatting.PlaceholderMaker):
    """ Ignores most data- attributes.
    """
    allowed = IgnoringDiffer.allowed

    def get_placeholder(self, element, ttype, close_ph):
        # remove attributes we don't want to diff
        if any(x.startswith('data-') for x in element.attrib):
            element = copy.copy(element)
            for k in list(element.attrib):
                if k.startswith('data-') and k not in self.allowed:
                    del element.attrib[k]
        return super().get_placeholder(element, ttype, close_ph)


class HTMLFormatter(formatting.XMLFormatter):
    """ Formats xmldiff output for HTML AKN documents.
    """
    xslt_filename = os.path.join(os.path.dirname(__file__), 'xmldiff.xslt')

    def __init__(self, normalize=formatting.WS_NONE, pretty_print=True, text_tags=(), formatting_tags=()):
        super().__init__(normalize, pretty_print, text_tags, formatting_tags)
        self.placeholderer = IgnoringPlaceholderMaker(
            text_tags=text_tags, formatting_tags=formatting_tags
        )

    def render(self, result):
        with open(self.xslt_filename) as f:
            xslt = lxml.etree.fromstring(f.read())
            transform = lxml.etree.XSLT(xslt)
        result = transform(result)

        # XSLT doesn't let us add an element to an attribute, so here
        # we move "classx" over onto "class"
        for node in result.xpath('//*[@classx]'):
            node.set('class', node.attrib.pop('classx'))

        # return the result as a tree, not as a string
        return result


class AKNHTMLDiffer:
    """ Helper class to diff AKN documents using xmldiff.
    """
    akn_text_tags = 'p listIntroduction listWrapUp heading subheading crossHeading'.split()
    html_text_tags = 'h1 h2 h3 h4 h5'.split()
    keep_ids_tags = AkomaNtoso30.hier_elements + ['table']
    formatter_class = HTMLFormatter
    differ_class = Differ
    preprocess_strip_tags = ['term']
    xmldiff_options = {
        'F': 0.75,
        # using data-refersto helps to xmldiff to handle definitions that move around
        'uniqueattrs': ['id', 'data-refersto'],
        'ratio_mode': 'faster',
        'fast_match': True,
    }

    def preprocess_xml_str(self, xml_str):
        """ Run pre-processing on XML before doing HTML diffs.
        """
        root = etree.fromstring(xml_str.encode('utf-8'))
        root = self.preprocess_xml_tree(root)
        return etree.tostring(root, encoding='utf-8')

    def preprocess_xml_tree(self, root):
        """ Run pre-processing on XML before doing HTML diffs. This helps to make the diffs less confusing.
        """
        xpath = '|'.join(f'//a:{x}' for x in self.preprocess_strip_tags)
        for elem in root.xpath(xpath, namespaces={'a': root.nsmap[None]}):
            unwrap_element(elem)
        return root

    def count_differences(self, diff_tree):
        """ Counts the number of differences in a diff tree."""
        return len(diff_tree.xpath('//ins|//del|//*[contains(@class, "ins") or contains(@class, "del")]'))

    def diff_html_str(self, old_html, new_html):
        """ Diffs two HTML strings for a single element and returns a string HTML diff.

        :return: None if there are no differences, otherwise a string with an HTML diff.
        """
        if not old_html and not new_html:
            return None

        if old_html == new_html:
            return None

        if not old_html:
            # it's newly added
            return '<div class="ins">' + new_html + '</div>'

        if not new_html:
            # it was deleted
            return '<div class="del">' + old_html + '</div>'

        parser = lxml.html.HTMLParser(encoding='utf-8')
        old_tree = lxml.html.fromstring(old_html.encode('utf-8'), parser=parser)
        new_tree = lxml.html.fromstring(new_html.encode('utf-8'), parser=parser)
        diff = self.diff_html(old_tree, new_tree)
        return lxml.html.tostring(diff, encoding='unicode')

    def diff_html(self, old_tree, new_tree):
        """ Compares two html trees, and returns a tree with annotated differences.
        """
        if old_tree is None:
            new_tree.tag = 'div'
            new_tree.classes.add('ins')
            return new_tree

        self.preprocess(old_tree)
        self.preprocess(new_tree)

        formatter = self.get_formatter()
        diff = self.diff_trees(old_tree, new_tree, formatter=formatter, diff_options=self.xmldiff_options)
        self.postprocess(diff)

        return diff

    def diff_trees(self, left, right, diff_options, formatter):
        """Takes two lxml root elements or element trees"""
        if formatter is not None:
            formatter.prepare(left, right)
        if diff_options is None:
            diff_options = {}
        differ = self.differ_class(**diff_options)
        diffs = differ.diff(left, right)

        if formatter is None:
            return list(diffs)

        return formatter.format(diffs, left)

    def get_formatter(self):
        # in html, AKN elements are recognised using classes
        text_tags = [f'*[@class="akn-{t}"]' for t in self.akn_text_tags] + self.html_text_tags
        return self.formatter_class(normalize=formatting.WS_NONE, pretty_print=False, text_tags=text_tags)

    def preprocess(self, tree):
        self.stash_ids(tree)

    def postprocess(self, tree):
        self.wrap_pairs(tree)
        self.unstash_ids(tree)
        self.strip_namespace(tree)

    def stash_ids(self, tree):
        """ Stashes id attributes for tags that they aren't actually useful for. Data- attributes are ignored,
        so it's save to move them there.
        """
        # ids should only be considered unique for these elements
        allow = set(f'akn-{t}' for t in self.keep_ids_tags)
        for node in tree.xpath('//*[@id]'):
            if node.attrib.get('class') not in allow:
                node.attrib['data-id'] = node.attrib.pop('id')

    def unstash_ids(self, tree):
        """ Restores id attributes stashed by stash_ids
        """
        for node in tree.xpath('//*[@data-id]'):
            node.attrib['id'] = node.attrib.pop('data-id')

    def wrap_pairs(self, diff):
        """ wrap del + ins pairs in <span class="diff-pair">
        """
        ws_re = re.compile(r'^ +| +$')
        for del_ in diff.iter('del'):
            pair = del_.makeelement('span', attrib={'class': 'diff-pair'})
            ins = del_.getnext()
            del_.addprevious(pair)
            pair.append(del_)

            # ensure leading and trailing text isn't hidden by the browser
            def repl(match):
                a, b = match.span()
                # non-breaking spaces
                return '\xA0' * (b - a)
            del_.text = ws_re.sub(repl, del_.text)

            if ins is None or ins.tag != 'ins' or del_.tail:
                ins = del_.makeelement('ins')
                # non-breaking space
                ins.text = '\xA0'
                ins.tail = del_.tail
                del_.tail = None
            pair.tail = ins.tail
            ins.tail = None

            pair.append(ins)

    def strip_namespace(self, tree):
        """ Strip the xmldiff namespace from the root of the tree.
        """
        etree.cleanup_namespaces(tree)


class AttributeDiffer:
    """ Differ that compares attributes and attribute dictionaries.
    """
    html_differ_class = AKNHTMLDiffer

    def __init__(self):
        self.html_differ = self.html_differ_class()

    def attr_title(self, attr):
        return attr.title().replace('_', ' ')

    def describe_differences(self, old_dict, new_dict, attrs):
        """ Describe differences in the listed attributes between old_dict and new_dict.

        Returns a list of difference dicts:

            attr: attr being compared
            title: attr in friendly title form
            type: 'str' or 'list'

        If type is 'str':
            old: old value
            new: new value
            html_old: old value as marked-up HTML
            html_new: new value as marked-up HTML

        If type is 'list':
            changes: list of changes as above, for 'str'

        """
        diffs = []

        for attr in attrs:
            title = self.attr_title(attr)
            old = old_dict.get(attr)
            new = new_dict.get(attr)

            cmp = self.diff_default
            if isinstance(old, list) or isinstance(new, list):
                cmp = self.diff_lists
            cmp = getattr(self, 'diff_attr_' + attr, cmp)

            diff = cmp(attr, title, old, new)
            if diff:
                diffs.append(diff)

        return diffs

    def diff_default(self, attr, title, old, new):
        if old != new:
            left, right = self.html_diff(old, new)
            return {
                'attr': attr,
                'title': title,
                'type': 'str',
                'old': old,
                'new': new,
                'html_old': left,
                'html_new': right,
            }

    def diff_lists(self, attr, title, old, new):
        old = old or []
        new = new or []
        if old == new:
            return

        diffs = [{
            'html_old': html.escape(x),
            'html_new': html.escape(x),
        } for x in old]

        # we're going to modify this
        old = list(old)
        remove_offset = 0

        for patch in jsonpatch.make_patch(old, new):
            # eg. "/0"
            index = int(patch['path'].split("/", 1)[1])

            if patch['op'] == 'add':
                v = patch['value']
                diffs.insert(index, {
                    'old': None,
                    'new': v,
                    'html_old': '',
                    'html_new': "<ins>{}</ins>".format(html.escape(v)),
                })
                # add a fake entry to old, because subsequent references will assume it has happened
                old.insert(index, None)
            elif patch['op'] == 'replace':
                old_v = old[index]
                new_v = patch['value']
                html_old, html_new = self.html_diff(old_v, new_v)
                diffs[index] = {
                    'old': old_v,
                    'new': new_v,
                    'html_old': html_old,
                    'html_new': html_new,
                }
            elif patch['op'] == 'remove':
                index += remove_offset
                v = old[index]
                diffs[index] = {
                    'old': v,
                    'new': None,
                    'html_old': "<del>{}</del>".format(html.escape(v)),
                    'html_new': '',
                }
                # subsequent remove operations will need to be offset
                remove_offset += 1

        return {
            'attr': attr,
            'title': title,
            'changes': diffs,
            'type': 'list',
        }

    def html_diff(self, old, new):
        """ Diff strings and return a left, right pair with HTML markup
        indicating differences.
        """
        if old is None:
            old = ''
        if new is None:
            new = ''
        old = str(old).replace('\n', ' ')
        new = str(new).replace('\n', ' ')

        left = []
        right = []

        matcher = SequenceMatcher(None, old, new)
        for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
            if opcode == 'equal':
                s = html.escape(matcher.a[a0:a1])
                left.append(s)
                right.append(s)

            elif opcode == 'insert':
                right.append('<ins>{}</ins>'.format(html.escape(matcher.b[b0:b1])))

            elif opcode == 'delete':
                left.append('<del>{}</del>'.format(html.escape(matcher.a[a0:a1])))

            elif opcode == 'replace':
                left.append('<del>{}</del>'.format(html.escape(matcher.a[a0:a1])))
                right.append('<ins>{}</ins>'.format(html.escape(matcher.b[b0:b1])))

        left = ''.join(left)
        right = ''.join(right)

        return left, right
