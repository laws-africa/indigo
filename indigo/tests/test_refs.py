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
          <p>As given in section 26(b), blah.</p>
          <p>As given in section 26(1)(b)(iii), blah.</p>
          <p>As given in section 26(1)(b)(iii)(bb), blah.</p>
          <p>As given in section 26(1)(b)(iii)(dd)(A), blah.</p>
          <p>As given in section 26B, blah.</p>
          <p>As given in section 26 and section 31, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26, blah.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Important heading</heading>
        <content>
          <p>An important provision.</p>
        </content>
      </section>
      <section id="section-26B">
        <num>26B.</num>
        <heading>Another important heading</heading>
        <content>
          <p>Another important provision.</p>
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
          <p>As given in <ref href="#section-26">section 26</ref>(b), blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref>(1)(b)(iii), blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref>(1)(b)(iii)(bb), blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref>(1)(b)(iii)(dd)(A), blah.</p>
          <p>As given in <ref href="#section-26B">section 26B</ref>, blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref> and <ref href="#section-31">section 31</ref>, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) <ref href="#section-26">section 26</ref>, blah.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Important heading</heading>
        <content>
          <p>An important provision.</p>
        </content>
      </section>
      <section id="section-26B">
        <num>26B.</num>
        <heading>Another important heading</heading>
        <content>
          <p>Another important provision.</p>
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
        self.assertEqual(expected.content, document.content)

    def test_section_of_this(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As given in section 26 of this Act, blah.</p>
          <p>As given in section 26 (1) of this Act, blah.</p>
          <p>As given in section 26 (1) of this Proclamation, blah.</p>
          <p>As given in section 26(1)(b)(iii)(dd)(A) of this Act, blah.</p>
          <p>In section 26 of Act 5 of 2012 it says one thing and in section 26 of this Act it says another.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26 of this Act, blah.</p>
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
          <p>As given in <ref href="#section-26">section 26</ref> of this Act, blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref> (1) of this Act, blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref> (1) of this Proclamation, blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref>(1)(b)(iii)(dd)(A) of this Act, blah.</p>
          <p>In section 26 of Act 5 of 2012 it says one thing and in <ref href="#section-26">section 26</ref> of this Act it says another.</p>
          <p>As <i>given</i> in (we're now in a tail) <ref href="#section-26">section 26</ref> of this Act, blah.</p>
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
        self.assertEqual(expected.content, document.content)

    def test_section_multiple(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As given in sections 26 and 31, blah.</p>
          <p>As given in sections 26, 26B, 30 and 31, blah.</p>
          <p>As given in section 26 or 31, blah.</p>
          <p>As given in sections 26 or 31, blah.</p>
          <p>As given in sections 26, 30(1) and 31, blah.</p>
          <p>As given in sections 26, 30 (1) and 31, blah.</p>
          <p>As given in sections 26(b), 30(1) or 31, blah.</p>
          <p>As given in section 26 (b), 30 (1) or 31, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26, 30 and 31.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Important heading</heading>
        <content>
          <p>An important provision.</p>
        </content>
      </section>
      <section id="section-26B">
        <num>26B.</num>
        <heading>Another important heading</heading>
        <content>
          <p>Another important provision.</p>
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
          <p>As given in sections <ref href="#section-26">26</ref> and <ref href="#section-31">31</ref>, blah.</p>
          <p>As given in sections <ref href="#section-26">26</ref>, <ref href="#section-26B">26B</ref>, <ref href="#section-30">30</ref> and <ref href="#section-31">31</ref>, blah.</p>
          <p>As given in section <ref href="#section-26">26</ref> or <ref href="#section-31">31</ref>, blah.</p>
          <p>As given in sections <ref href="#section-26">26</ref> or <ref href="#section-31">31</ref>, blah.</p>
          <p>As given in sections <ref href="#section-26">26</ref>, <ref href="#section-30">30</ref>(1) and <ref href="#section-31">31</ref>, blah.</p>
          <p>As given in sections <ref href="#section-26">26</ref>, <ref href="#section-30">30</ref> (1) and <ref href="#section-31">31</ref>, blah.</p>
          <p>As given in sections <ref href="#section-26">26</ref>(b), <ref href="#section-30">30</ref>(1) or <ref href="#section-31">31</ref>, blah.</p>
          <p>As given in section <ref href="#section-26">26</ref> (b), <ref href="#section-30">30</ref> (1) or <ref href="#section-31">31</ref>, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) section <ref href="#section-26">26</ref>, <ref href="#section-30">30</ref> and <ref href="#section-31">31</ref>.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>Important heading</heading>
        <content>
          <p>An important provision.</p>
        </content>
      </section>
      <section id="section-26B">
        <num>26B.</num>
        <heading>Another important heading</heading>
        <content>
          <p>Another important provision.</p>
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
        self.assertEqual(expected.content, document.content)

    def test_section_invalid(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As given in section 25, which isn't in this document, blah.</p>
          <p>In section 200 it says one thing and in section 26 of Act 5 of 2012 it says another.</p>
          <p>As given in section 26(1)(a) of Proclamation 9 of 1926, blah.</p>
          <p>As per Proclamation 9 of 1926, as given in section 26 thereof, blah.</p>
          <p>As per Proclamation 9 of 1926, as given in section 26 of that Proclamation, blah.</p>
          <p>As per Act 9 of 2005, as given in section 26 of that Act, blah.</p>
          <p>As given in section 26(1)(b)(iii)(dd)(A) of Act 5 of 2002, blah.</p>
          <p>As given in section 26 of Act 5 of 2012, blah.</p>
          <p>As given in section 26 of the Nursing Act, blah.</p>
          <p>As given in section 26(b) of the Nursing Act, blah.</p>
          <p>As given in section 26(b)(iii) of the Nursing Act, blah.</p>
          <p>As given in section 26 (b) (iii) of the Nursing Act, blah.</p>
          <p>As given in section 26(b)(iii)(bb) of the Nursing Act, blah.</p>
          <p>As given in section 26(b)(iii)(aa)(A) of the Nursing Act, blah.</p>
          <p>As given in section 26, 27 or 28(b) of the Nursing Act, blah.</p>
          <p>As given in section 26 or 27 of the Nursing Act, blah.</p>
          <p>As given in section 26(b)(iii)(1) of the Nursing Act, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26 of Act 5 of 2012, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26 of the Nursing Act, blah.</p>
          <p>As <i>given</i> in (we're now in a tail) sections 26, 27 and 28 of the Nursing Act, blah.</p>
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

        expected_content = document.content
        self.section_refs_finder.find_references_in_document(document)
        root = etree.fromstring(expected_content)
        expected_content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(expected_content, document.content)

    def test_section_valid_and_invalid(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As given in sections 26 and 35, one of which isn't in this document, blah.</p>
          <p>As given in sections 35 and 26, one of which isn't in this document, blah.</p>
          <p>In section 200 it says one thing and in section 26 it says another.</p>
          <p>As <i>given</i> in (we're now in a tail) section 200, blah, but section 26 says something else.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26 of Act 5 of 2012, blah, but section 26 of this Act says something else.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>The section we want</heading>
        <content>
          <p>The provision you're looking for.</p>
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
          <p>As given in sections <ref href="#section-26">26</ref> and 35, one of which isn't in this document, blah.</p>
          <p>As given in sections 35 and <ref href="#section-26">26</ref>, one of which isn't in this document, blah.</p>
          <p>In section 200 it says one thing and in <ref href="#section-26">section 26</ref> it says another.</p>
          <p>As <i>given</i> in (we're now in a tail) section 200, blah, but <ref href="#section-26">section 26</ref> says something else.</p>
          <p>As <i>given</i> in (we're now in a tail) section 26 of Act 5 of 2012, blah, but <ref href="#section-26">section 26</ref> of this Act says something else.</p>
        </content>
      </section>
      <section id="section-26">
        <num>26.</num>
        <heading>The section we want</heading>
        <content>
          <p>The provision you're looking for.</p>
        </content>
      </section>
        """
            ),
            language=self.eng)

        self.section_refs_finder.find_references_in_document(document)
        root = etree.fromstring(expected.content)
        expected_content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(expected_content, document.content)

    def test_section_edge(self):
        document = Document(
            document_xml=document_fixture(
                xml="""
      <section id="section-1">
        <num>1.</num>
        <heading>Unimportant heading</heading>
        <content>
          <p>An unimportant provision.</p>
        </content>
      </section>
      <section id="section-2">
        <num>2.</num>
        <heading>Unimportant heading</heading>
        <content>
          <p>An unimportant provision.</p>
        </content>
      </section>
      <section id="section-3">
        <num>3.</num>
        <heading>Unimportant heading</heading>
        <content>
          <p>An unimportant provision.</p>
        </content>
      </section>
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As given in section 26(1), blah.</p>
          <p>As given in section 26 (1), blah.</p>
          <p>As given in section 26(1), (2) and (3), blah.</p>
          <p>As given in section 26 (1), (2) and (3), blah.</p>
          <p>As given in sections 26(1), (2) and (3), blah.</p>
          <p>As given in sections 26 (1), (2) and (3), blah.</p>
          <p>As given in section 26 (2) and (3), blah.</p>
          <p>As given in section 26(2) and (3), blah.</p>
          <p>As given in sections 26 (2) and (3), blah.</p>
          <p>As given in sections 26(2) and (3), blah.</p>
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
      <section id="section-1">
        <num>1.</num>
        <heading>Unimportant heading</heading>
        <content>
          <p>An unimportant provision.</p>
        </content>
      </section>
      <section id="section-2">
        <num>2.</num>
        <heading>Unimportant heading</heading>
        <content>
          <p>An unimportant provision.</p>
        </content>
      </section>
      <section id="section-3">
        <num>3.</num>
        <heading>Unimportant heading</heading>
        <content>
          <p>An unimportant provision.</p>
        </content>
      </section>
      <section id="section-7">
        <num>7.</num>
        <heading>Active ref heading</heading>
        <content>
          <p>As given in <ref href="#section-26">section 26</ref>(1), blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref> (1), blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref>(1), (2) and (3), blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref> (1), (2) and (3), blah.</p>
          <p>As given in <ref href="#section-26">sections 26</ref>(1), (2) and (3), blah.</p>
          <p>As given in <ref href="#section-26">sections 26</ref> (1), (2) and (3), blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref> (2) and (3), blah.</p>
          <p>As given in <ref href="#section-26">section 26</ref>(2) and (3), blah.</p>
          <p>As given in <ref href="#section-26">sections 26</ref> (2) and (3), blah.</p>
          <p>As given in <ref href="#section-26">sections 26</ref>(2) and (3), blah.</p>
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
        self.assertEqual(expected.content, document.content)
