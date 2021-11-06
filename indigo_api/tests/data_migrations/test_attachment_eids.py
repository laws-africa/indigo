from django.test import TestCase
from lxml import etree

from indigo_api.models import Document, Work
from indigo_api.data_migrations import CorrectAttachmentEids
from indigo_api.tests.fixtures import component_fixture


class MigrationTestCase(TestCase):
    maxDiff = None

    def test_simple(self):
        migration = CorrectAttachmentEids()

        xml = component_fixture(xml="""<section eId="sec_1"><heading>Section</heading><content><p eId="sec_1__p_1">text</p></content></section>""")
        work = Work(frbr_uri='/akn/za/act/2009/1')
        doc = Document(document_xml=xml, work=work)
        migration.migrate_document(doc)

        self.assertMultiLineEqual(
            component_fixture(xml="""<section eId="att_1__sec_1"><heading>Section</heading><content><p eId="att_1__sec_1__p_1">text</p></content></section>"""),
            etree.tostring(doc.doc.root, encoding='utf-8', pretty_print=True).decode('utf-8'))
        self.assertEqual({
            'sec_1': 'att_1__sec_1',
            'sec_1__p_1': 'att_1__sec_1__p_1',
        }, migration.eid_mappings)
