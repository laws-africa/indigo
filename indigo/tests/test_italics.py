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
        self.italics_terms = ['ad', 'ad hoc', 'ad idem', 'Gazette', 'Government Gazette', 'habeus corpus', 'per']
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

    def test_italics_repeated_terms(self):
        """ Checks that if a word is both an italics term and part of a longer italics term,
        both are marked up appropriately.
        """
        document = Document(
            work=self.work,
            document_xml=document_fixture(
                xml="""
        <section id="section-1">
          <num>1.</num>
          <heading>Notification in Gazette</heading>
          <content>
            <p>In the Government Gazette it says:</p>
            <p>that advertising executives should be ad idem.</p>
            <p>However, ad something else and ad hoc policies</p>
            <p>should be discouraged. The Gazetted text is clear on this</p>
            <p>(in case of doubt check the Gazette).</p>
            <p>Both Gazette and Government Gazette should be italicised.</p>
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
          <heading>Notification in <i>Gazette</i></heading>
          <content>
            <p>In the <i>Government Gazette</i> it says:</p>
            <p>that advertising executives should be <i>ad idem</i>.</p>
            <p>However, <i>ad</i> something else and <i>ad hoc</i> policies</p>
            <p>should be discouraged. The Gazetted text is clear on this</p>
            <p>(in case of doubt check the <i>Gazette</i>).</p>
            <p>Both <i>Gazette</i> and <i>Government Gazette</i> should be italicised.</p>
          </content>
        </section>
                """
            )
        )

        self.italics_terms_finder.mark_up_italics_in_document(document, self.italics_terms)
        root = etree.fromstring(expected.content)
        expected.content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(expected.content, document.content)
