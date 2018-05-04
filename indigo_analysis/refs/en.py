import re
from lxml import etree

from .base import BaseRefsFinder


class RefsFinderEN(BaseRefsFinder):
    """ Finds references to Acts in documents, of the form:

        Act 52 of 2001
        Act no. 52 of 1998
    """

    # country, language, locality
    locale = (None, 'eng', None)

    act_re = re.compile(r'Act,?\s+(no\.?\s*)?(\d+)+\s+of\s+(\d{4})', re.I)
    # the ancestor elements that can contain references
    ancestors = ['coverpage', 'preface', 'preamble', 'body', 'mainBody', 'conclusions']

    def __init__(self):
        self.ancestor_xpath = '|'.join('.//a:%s' % a for a in self.ancestors)

    def find_references_in_document(self, document):
        """ Find references in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content)
        self.find_references(root, document.doc.frbr_uri)
        document.content = etree.tostring(root, encoding='UTF-8')

    def find_references(self, root, frbr_uri):
        ns = root.nsmap[None]
        act_xpath = etree.XPath(".//text()[contains(., 'Act') and not(ancestor::a:ref)]", namespaces={'a': ns})

        def make_ref(match):
            ref = etree.Element("{%s}ref" % ns)
            ref.text = match.group()
            ref.set('href', '/%s/act/%s/%s' % (frbr_uri.country, match.group(3), match.group(2)))
            return ref

        for root in root.xpath(self.ancestor_xpath, namespaces={'a': ns}):
            for candidate in act_xpath(root):
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

                while node is not None:
                    match = self.act_re.search(node.tail)
                    if not match:
                        break

                    ref = make_ref(match)
                    node.addnext(ref)
                    node.tail = match.string[:match.start()]
                    ref.tail = match.string[match.end():]

                    # now continue to check the new tail
                    node = ref
