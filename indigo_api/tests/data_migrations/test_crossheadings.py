from django.test import TestCase
from lxml import etree

from indigo_api.models import Document, Work
from indigo_api.data_migrations import RealCrossHeadings
from indigo_api.tests.fixtures import document_fixture


class MigrationTestCase(TestCase):
    maxDiff = None

    def test_simple(self):
        migration = RealCrossHeadings()

        xml = document_fixture(xml="""<hcontainer eId="hcontainer_1" name="crossheading"><heading>In the body</heading></hcontainer>""")
        work = Work(frbr_uri='/akn/za/act/2009/1')
        doc = Document(document_xml=xml, work=work)
        migration.migrate_document(doc)

        expected = document_fixture(xml="""<crossHeading eId="crossHeading_1">In the body</crossHeading>""")
        self.assertMultiLineEqual(
            expected,
            etree.tostring(doc.doc.root, encoding='utf-8', pretty_print=True).decode('utf-8'))
        self.assertEqual({
            'hcontainer_1': 'crossHeading_1',
        }, migration.eid_mappings)

    def test_multiple(self):
        migration = RealCrossHeadings()

        xml = document_fixture(xml="""<section eId="sec_1"><num>1</num>
  <hcontainer eId="sec_1__hcontainer_1" name="crossheading"><heading>First crossheading</heading></hcontainer>
  <hcontainer eId="sec_1__hcontainer_2"><content><p eId="sec_1__hcontainer_2__p_1">some text</p></content></hcontainer>
  <hcontainer eId="sec_1__hcontainer_3" name="crossheading"><heading>Second crossheading</heading></hcontainer>
</section>""")
        work = Work(frbr_uri='/akn/za/act/2009/1')
        doc = Document(document_xml=xml, work=work)
        migration.migrate_document(doc)

        expected = document_fixture(xml="""<section eId="sec_1"><num>1</num>
  <crossHeading eId="sec_1__crossHeading_1">First crossheading</crossHeading>
  <hcontainer eId="sec_1__hcontainer_1"><content><p eId="sec_1__hcontainer_1__p_1">some text</p></content></hcontainer>
  <crossHeading eId="sec_1__crossHeading_2">Second crossheading</crossHeading>
</section>""")
        self.assertMultiLineEqual(
            expected,
            etree.tostring(doc.doc.root, encoding='utf-8', pretty_print=True).decode('utf-8'))
        self.assertEqual({
            'sec_1__hcontainer_1': 'sec_1__crossHeading_1',
            'sec_1__hcontainer_2': 'sec_1__hcontainer_1',
            'sec_1__hcontainer_2__p_1': 'sec_1__hcontainer_1__p_1',
            'sec_1__hcontainer_3': 'sec_1__crossHeading_2',
        }, migration.eid_mappings)
