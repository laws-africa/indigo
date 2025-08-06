import asyncio
import copy
import os
import re
import tempfile
import logging

import lxml.html
from lxml import etree
from xmldiff import formatting
from xmldiff.diff import Differ
from cobalt.schemas import AkomaNtoso30
from docpipe.xmlutils import unwrap_element
from indigo.xmlutils import parse_html_str

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

    def is_formatting(self, element):
        return element.get('class') in ['akn-remark']


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

        old_tree = parse_html_str(old_html)
        new_tree = parse_html_str(new_html)
        diff = self.diff_html(old_tree, new_tree)
        return lxml.html.tostring(diff, encoding='unicode')

    async def adiff_html_str(self, old_html, new_html):
        """ Diffs two HTML strings for a single element and returns a string HTML diff.

        This runs asynchronously to avoid blocking.

        :return: None if there are no differences, otherwise a string with an HTML diff.
        """
        if old_html == new_html:
            return None

        if not old_html:
            # it's newly added
            return '<div class="ins">' + new_html + '</div>'

        if not new_html:
            # it was deleted
            return '<div class="del">' + old_html + '</div>'

        with tempfile.NamedTemporaryFile() as f1, tempfile.NamedTemporaryFile() as f2:
            f1.write(old_html.encode('utf-8'))
            f1.flush()
            f2.write(new_html.encode('utf-8'))
            f2.flush()

            # do the actual diff in a subprocess
            log.debug("Running diff_akn on %s and %s", f1.name, f2.name)
            proc = await asyncio.create_subprocess_exec(
                "python", "-m", "indigo_lib.diff_akn", f1.name, f2.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()
            log.debug("diff_akn finished with return code %d", proc.returncode)
            return stdout.decode('utf-8')

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

            if del_.tail or ins is None or (ins.tag != 'ins' and not (ins.get('class') or '').startswith('ins ')):
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
