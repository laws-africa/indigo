# -*- coding: utf-8 -*-
from lxml import etree

from django.test import TestCase

from indigo.analysis.italics_terms import BaseItalicsFinder
from indigo_api.models import Document, Work
from indigo_api.tests.fixtures import document_fixture


class ItalicsMarkupTestCase(TestCase):

    def setUp(self):
        self.work = Work(frbr_uri='/za/act/1991/1')
        self.italics_terms_finder = BaseItalicsFinder()
        self.italics_terms = ['Gazette', 'habeus corpus', 'per']
        self.maxDiff = None

    def test_italics_markup(self):
        document = Document(
            work=self.work,
            document_xml=document_fixture(
                xml="""
        <section id="section-1">
          <num>1.</num>
          <heading>Application of Act</heading>
          <content>
            <p>In the Gazette it says that habeus corpus is XYZ. As per the evidence of person X, Y.</p>
          </content>
        </section>
                """
            )
        )

        expected = Document(
            work=self.work,
            document_xml=document_fixture(
                xml="""
        <section id="section-1">
          <num>1.</num>
          <heading>Application of Act</heading>
          <content>
            <p>In the <i>Gazette</i> it says that <i>habeus corpus</i> is XYZ. As <i>per</i> the evidence of person X, Y.</p>
          </content>
        </section>
                """
            )
        )

        self.italics_terms_finder.mark_up_italics_in_document(document, self.italics_terms)
        root = etree.fromstring(expected.content)
        expected.content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(expected.content, document.content)
