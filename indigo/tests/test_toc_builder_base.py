# -*- coding: utf-8 -*-
from django.test import TestCase

from indigo_api.tests.fixtures import document_fixture, component_fixture
from indigo_api.models import Document, Language, Work

from indigo.analysis.toc.base import TOCBuilderBase


class TOCBuilderBaseTestCase(TestCase):
    fixtures = ['languages_data', 'countries']

    def setUp(self):
        self.work = Work(frbr_uri='/za/act/1998/1')
        self.builder = TOCBuilderBase()
        self.eng = Language.for_code('eng')

    def test_toc_simple(self):
        doc = Document(
            work=self.work,
            document_xml=document_fixture(text="hi"),
            language=self.eng)

        toc = self.builder.table_of_contents_for_document(doc)
        self.assertEqual([t.as_dict() for t in toc], [{
            'component': 'main',
            'title': 'Section',
            'type': 'section',
            'id': 'sec_1',
            'subcomponent': 'section'
        }])

    def test_toc_item_simple(self):
        doc = Document(
            work=self.work,
            document_xml=document_fixture(text="hi"),
            language=self.eng)

        elem = doc.doc.root.xpath("//*[@eId='sec_1']")[0]

        toc = self.builder.table_of_contents_entry_for_element(doc, elem)
        self.assertEqual(toc.as_dict(), {
            'component': 'main',
            'title': 'Section',
            'type': 'section',
            'id': 'sec_1',
            'subcomponent': 'section'
        })

    def test_toc_item_in_schedule(self):
        doc = Document(
            work=self.work,
            document_xml=component_fixture(text="hi"),
            language=self.eng)

        elem = doc.doc.root.xpath("//*[@eId='sec_1']")[0]

        toc = self.builder.table_of_contents_entry_for_element(doc, elem)
        self.assertEqual(toc.as_dict(), {
            'component': 'schedule',
            'title': 'Section',
            'type': 'section',
            'id': 'sec_1',
            'subcomponent': 'section'
        })
