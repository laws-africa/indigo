# -*- coding: utf-8 -*-
from lxml import etree

from django.test import TestCase

from indigo_api.models import Document, Language
from indigo_api.tests.fixtures import document_fixture
from indigo.analysis.refs.base import SectionRefsFinderENG


class SectionRefsFinderTestCase(TestCase):
    fixtures = ['countries']

    def setUp(self):
        self.section_refs_finder = SectionRefsFinderENG()
        self.eng = Language.for_code('eng')

    def test_section_basic(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Section 7 heading</heading>
        <content>
          <p>As given in section 26, blah.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Section 26 heading</heading>
        <content>
          <p>An important provision.</p>
        </content>
      </section>
        """
            ),
            language=self.eng)

        expected = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Section 7 heading</heading>
        <content>
          <p>As given in section <ref href="#section-26">26</ref>, blah.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Section 26 heading</heading>
        <content>
          <p>An important provision.</p>
        </content>
      </section>
        """
            ),
            language=self.eng)

        self.section_refs_finder.find_references_in_document(document)
        root = etree.fromstring(expected.content)
        expected.content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(document.content, expected.content)
