import os
from lxml import etree

from django.test import TestCase

from indigo.xmlutils import EIdRewriter, rewrite_ids


class EIdRewriterTestCase(TestCase):
    maxDiff = None

    def rewrite_eids(self, xml):
        """ rewrite eIds created by slaw that are guaranteed to be unique,
         and use `nn` to indicate unnumbered elements.
         Copied from indigo_api.Importer for testing.
        """
        root = etree.fromstring(xml)
        ns = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
        ids = EIdRewriter(ns)
        skip_entirely = ['meta']

        def rewrite(prefix, item):
            name = item.tag.replace(f'{{{ns}}}', '')
            existing = item.get('eId')
            if name not in skip_entirely:
                if existing:
                    new = ids.make(prefix, item, name)
                    if existing != new:
                        rewrite_ids(item, existing, new)

                for e in item:
                    rewrite(item.get('eId', prefix), e)

        rewrite('', root)

        return etree.tostring(root, encoding='utf-8').decode('utf-8')

    def run_it(self, fname_in, fname_out):
        dir = os.path.join(os.path.dirname(__file__), 'eid_fixtures')
        fname = os.path.join(dir, f'{fname_in}.xml')
        with open(fname, 'rt') as f:
            xml = f.read()
        xml_out = self.rewrite_eids(xml)

        fname = os.path.join(dir, f'{fname_out}.xml')
        with open(fname, 'rt') as f:
            xml = f.read()

        self.assertEqual(xml_out, xml)

    def test_unchanged(self):
        self.run_it('unchanged', 'unchanged')
