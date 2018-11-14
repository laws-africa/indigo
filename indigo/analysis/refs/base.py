from __future__ import absolute_import
from lxml import etree
import re

from indigo.plugins import LocaleBasedMatcher, plugins


class BaseRefsFinder(LocaleBasedMatcher):
    """ Finds references to Acts in documents.

    Subclasses must implement `find_references_in_document`.
    """

    act_re = None  # this must be defined by a subclass
    candidate_xpath = None  # this must be defined by a subclass

    # the ancestor elements that can contain references
    ancestors = ['coverpage', 'preface', 'preamble', 'body', 'mainBody', 'conclusions']

    def find_references_in_document(self, document):
        """ Find references in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content)
        self.frbr_uri = document.doc.frbr_uri
        self.setup(root)
        self.find_references(root)
        document.content = etree.tostring(root, encoding='UTF-8')

    def setup(self, root):
        self.ns = root.nsmap[None]
        self.nsmap = {'a': self.ns}
        self.ref_tag = "{%s}ref" % self.ns

        self.ancestor_xpath = etree.XPath('|'.join('.//a:%s' % a for a in self.ancestors), namespaces=self.nsmap)
        self.candidate_xpath = etree.XPath(self.candidate_xpath, namespaces=self.nsmap)

    def make_href(self, match):
        """ Turn this match into a full FRBR URI href
        """
        raise NotImplementedError("Subclass must implement based on act_re")

    def find_references(self, root):
        def make_ref(match):
            ref = etree.Element(self.ref_tag)
            ref.text = match.group()
            ref.set('href', self.make_href(match))
            return ref

        for root in self.ancestor_xpath(root):
            for candidate in self.candidate_xpath(root):
                node = candidate.getparent()

                if not candidate.is_tail:
                    # text directly inside a node
                    match = self.act_re.search(node.text)
                    if match:
                        ref = make_ref(match)
                        node.text = match.string[:match.start()]
                        node.insert(0, ref)
                        ref.tail = match.string[match.end():]

                        # now continue to check the new tail
                        node = ref

                while node is not None and node.tail:
                    match = self.act_re.search(node.tail)
                    if not match:
                        break

                    ref = make_ref(match)
                    node.addnext(ref)
                    node.tail = match.string[:match.start()]
                    ref.tail = match.string[match.end():]

                    # now continue to check the new tail
                    node = ref


@plugins.register('refs')
class RefsFinderENG(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Act 52 of 2001
        Act no. 52 of 1998
        Income Tax Act, 1962 (No 58 of 1962)

    """

    # country, language, locality
    locale = (None, 'eng', None)

    # if this changes, update indigo_za/refs.py
    act_re = re.compile(r'\bAct,?\s+(\d{4}\s+)?(\()?([nN]o\.?\s*)?(\d+)\s+of\s+(\d{4})')
    candidate_xpath = ".//text()[contains(., 'Act') and not(ancestor::a:ref)]"

    def make_href(self, match):
        year = match.group(4)
        number = match.group(3)
        return '/%s/act/%s/%s' % (self.frbr_uri.country, year, number)
