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
        self.maxDiff = None

    def test_section_basic(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As given in section 26, blah.</p>
          <p>As given in section 26 and section 31, blah.</p>
          <p>As given in section 26 of this Act, blah.</p>
          <p>In section 200 it says one thing and section 26 it says another.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Important heading</heading>
        <content>
          <p>An important provision.</p>
        </content>
      </section>
      <section id="section-30">
        <num>30.</num>
        <heading>Less important</heading>
        <content>
          <p>Meh.</p>
        </content>
      </section>
      <section id="section-31">
        <num>31.</num>
        <heading>More important</heading>
        <content>
          <p>Hi!</p>
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
        <heading>Active ref heading</heading>
        <content>
          <p>As given in <ref href="#section-26">section 26</ref>, blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref> and <ref href="#section-31">section 31</ref>, blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref> of this Act, blah.</p>
          <p>In section 200 it says one thing and <ref href="#section-26">section 26</ref> it says another.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Important heading</heading>
        <content>
          <p>An important provision.</p>
        </content>
      </section>
      <section id="section-30">
        <num>30.</num>
        <heading>Less important</heading>
        <content>
          <p>Meh.</p>
        </content>
      </section>
      <section id="section-31">
        <num>31.</num>
        <heading>More important</heading>
        <content>
          <p>Hi!</p>
        </content>
      </section>
        """
            ),
            language=self.eng)

        self.section_refs_finder.find_references_in_document(document)
        root = etree.fromstring(expected.content)
        expected.content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(document.content, expected.content)

    def test_section_basic_in_tail(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As <i>given</i> in (we're now in a tail) section 26, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26 of this Act, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) section 200, blah, but section 26 says something else.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26 of Act 5 of 2012, blah, but section 26 of this Act says something else.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Important heading</heading>
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
        <heading>Active ref heading</heading>
        <content>
          <p>As <i>given</i> in (we're now in a tail) <ref href="#section-26">section 26</ref>, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) <ref href="#section-26">section 26</ref> of this Act, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) section 200, blah, but <ref href="#section-26">section 26</ref> says something else.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26 of Act 5 of 2012, blah, but <ref href="#section-26">section 26</ref> of this Act says something else.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Important heading</heading>
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

    def test_section_notfound(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As given in section 26, which isn't in this document, blah.</p>
        </content>
      </section>
      <section id="section-35">
        <num>35.</num>
        <heading>Not the section we want</heading>
        <content>
          <p>Not the provision you're looking for.</p>
        </content>
      </section>
        """
            ),
            language=self.eng)

        expected_content = document.content
        self.section_refs_finder.find_references_in_document(document)
        root = etree.fromstring(expected_content)
        expected_content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(document.content, expected_content)

    def test_section_external(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As given in section 26 of Act 5 of 2012, blah.</p>
          <p>As given in section 26 of the Nursing Act, blah.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Passive ref heading</heading>
        <content>
          <p>An important provision, but not the one referred to above.</p>
        </content>
      </section>
        """
            ),
            language=self.eng)

        expected_content = document.content
        self.section_refs_finder.find_references_in_document(document)
        root = etree.fromstring(expected_content)
        expected_content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(document.content, expected_content)

    def test_section_external_in_tail(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As <i>given</i> in (we're now in a tail) section 26 of Act 5 of 2012, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26 of the Nursing Act, blah.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Passive ref heading</heading>
        <content>
          <p>An important provision, but not the one referred to above.</p>
        </content>
      </section>
        """
            ),
            language=self.eng)

        expected_content = document.content
        self.section_refs_finder.find_references_in_document(document)
        root = etree.fromstring(expected_content)
        expected_content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(document.content, expected_content)
