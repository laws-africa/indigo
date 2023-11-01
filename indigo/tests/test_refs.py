from lxml import etree

from django.conf import settings
from django.test import TestCase

from cobalt import FrbrUri

from indigo.analysis.refs.base import RefsFinderENG, RefsFinderSubtypesENG, RefsFinderCapENG

from indigo_api.models import Document, Language, Work, Country, User
from indigo_api.tests.fixtures import document_fixture


class RefsFinderENGTestCase(TestCase):
    fixtures = ['languages_data', 'countries']

    def setUp(self):
        self.work = Work(frbr_uri='/akn/za/act/1991/1')
        self.finder = RefsFinderENG()
        self.eng = Language.for_code('eng')
        self.maxDiff = None

    def test_find_simple(self):
        document = Document(
            work=self.work,
            document_xml=document_fixture(
                xml="""
        <section eId="sec_1">
          <num>1.</num>
          <heading>Tester</heading>
          <paragraph eId="sec_1.paragraph-0">
            <content>
              <p>Something to do with Act no 22 of 2012.</p>
              <p>And another thing about Act 4 of 1998.</p>
            </content>
          </paragraph>
        </section>"""
            ),
            language=self.eng)

        expected = Document(
            work=self.work,
            document_xml=document_fixture(
                xml="""
        <section eId="sec_1">
          <num>1.</num>
          <heading>Tester</heading>
          <paragraph eId="sec_1.paragraph-0">
            <content>
              <p>Something to do with Act <ref href="/akn/za/act/2012/22">no 22 of 2012</ref>.</p>
              <p>And another thing about Act <ref href="/akn/za/act/1998/4">4 of 1998</ref>.</p>
            </content>
          </paragraph>
        </section>"""
            ),
            language=self.eng)

        self.finder.find_references_in_document(document)
        root = etree.fromstring(expected.content)
        expected.content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(expected.content, document.content)

    def test_dont_find_self(self):
        document = Document(
            work=self.work,
            frbr_uri=self.work.frbr_uri,
            document_xml=document_fixture(
                xml="""
        <section eId="sec_1">
          <num>1.</num>
          <heading>Tester</heading>
          <paragraph eId="sec_1.paragraph-0">
            <content>
              <p>Something to do with Act 1 of 1991.</p>
              <p>Something to do with Act no 22 of 2012.</p>
              <p>And another thing about Act 4 of 1998.</p>
            </content>
          </paragraph>
        </section>"""
            ),
            language=self.eng)

        expected = Document(
            work=self.work,
            document_xml=document_fixture(
                xml="""
        <section eId="sec_1">
          <num>1.</num>
          <heading>Tester</heading>
          <paragraph eId="sec_1.paragraph-0">
            <content>
              <p>Something to do with Act 1 of 1991.</p>
              <p>Something to do with Act <ref href="/akn/za/act/2012/22">no 22 of 2012</ref>.</p>
              <p>And another thing about Act <ref href="/akn/za/act/1998/4">4 of 1998</ref>.</p>
            </content>
          </paragraph>
        </section>"""
            ),
            language=self.eng)

        document.doc.frbr_uri = FrbrUri.parse(self.work.frbr_uri)
        self.finder.find_references_in_document(document)
        root = etree.fromstring(expected.content)
        expected.content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(expected.content, document.content)


class RefsFinderSubtypesENGTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'subtype']

    def setUp(self):
        self.work = Work(frbr_uri='/akn/za/act/1991/1')
        self.finder = RefsFinderSubtypesENG()
        self.eng = Language.for_code('eng')
        self.maxDiff = None

    def test_find_simple(self):
        document = Document(
            work=self.work,
            document_xml=document_fixture(
                xml="""
        <section eId="sec_1">
          <num>1.</num>
          <heading>Tester</heading>
          <paragraph eId="sec_1.paragraph-0">
            <content>
              <p>Something to do with GN no 102 of 2012.</p>
              <p>And another thing about SI 4 of 1998.</p>
            </content>
          </paragraph>
        </section>"""
            ),
            language=self.eng)

        expected = Document(
            work=self.work,
            document_xml=document_fixture(
                xml="""
        <section eId="sec_1">
          <num>1.</num>
          <heading>Tester</heading>
          <paragraph eId="sec_1.paragraph-0">
            <content>
              <p>Something to do with <ref href="/akn/za/act/gn/2012/102">GN no 102 of 2012</ref>.</p>
              <p>And another thing about <ref href="/akn/za/act/si/1998/4">SI 4 of 1998</ref>.</p>
            </content>
          </paragraph>
        </section>"""
            ),
            language=self.eng)

        self.finder.find_references_in_document(document)
        root = etree.fromstring(expected.content)
        expected.content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(expected.content, document.content)


class RefsFinderCapENGTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user']

    def setUp(self):
        self.finder = RefsFinderCapENG()
        self.eng = Language.for_code('eng')
        self.maxDiff = None

    def test_find_simple(self):
        za = Country.objects.get(pk=1)
        user1 = User.objects.get(pk=1)
        settings.INDIGO['WORK_PROPERTIES'] = {
            'za': {
                'cap': 'Chapter (cap)',
            }
        }

        work = Work(
            frbr_uri='/akn/za/act/2002/5',
            title='Act 5 of 2002',
            country=za,
            created_by_user=user1,
        )
        work.properties['cap'] = '12'
        work.updated_by_user = user1
        work.save()

        document = Document(
            document_xml=document_fixture(
                xml="""
        <section eId="sec_1">
          <num>1.</num>
          <heading>Tester</heading>
          <paragraph eId="sec_1.paragraph-0">
            <content>
              <p>Something to do with Cap. 12.</p>
            </content>
          </paragraph>
        </section>"""
            ),
            language=self.eng,
            work=work)

        expected = Document(
            document_xml=document_fixture(
                xml="""
        <section eId="sec_1">
          <num>1.</num>
          <heading>Tester</heading>
          <paragraph eId="sec_1.paragraph-0">
            <content>
              <p>Something to do with <ref href="/akn/za/act/2002/5">Cap. 12</ref>.</p>
            </content>
          </paragraph>
        </section>"""
            ),
            language=self.eng,
            work=work)

        self.finder.find_references_in_document(document)
        root = etree.fromstring(expected.content)
        expected.content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(expected.content, document.content)
        # set back to what it is in settings.py
        settings.INDIGO['WORK_PROPERTIES'] = {}
