import unittest.util
from unittest.mock import patch

from django.test import TestCase
from lxml import etree

from cobalt import AkomaNtosoDocument, FrbrUri
from docpipe.matchers import ExtractedCitation

from indigo.analysis.refs.provisions import ProvisionRefsResolver, ProvisionRef, ProvisionRefsMatcher, parse_provision_refs, MainProvisionRef
from indigo.xmlutils import parse_html_str
from indigo_api.tests.fixtures import document_fixture, component_fixture


unittest.util._MAX_LENGTH = 999999999


class ProvisionRefsResolverTestCase(TestCase):
    maxDiff = None

    def resolve_references_str(self, text: str, root, lang_code='eng'):
        """Parse a string into reference objects, and the resolve them to eIds in the given root element."""
        refs = parse_provision_refs(text, lang_code).references
        for ref in refs:
            self.resolver.resolve_references(ref, root)
        return refs

    def setUp(self):
        self.resolver = ProvisionRefsResolver()
        self.doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_1">
              <num>1.</num>
              <subsection eId="sec_1__subsec_1">
                <num>(1)</num>
                <paragraph eId="sec_1__subsec_1__para_a">
                  <num>(a)</num>
                </paragraph>
                <paragraph eId="sec_1__subsec_1__para_b">
                  <num>(b)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_1__subsec_2">
                <num>(2)</num>
              </subsection>
            </section>
            <section eId="sec_2">
              <num>2.</num>
              <subsection eId="sec_2__subsec_1">
                <num>(1)</num>
                <paragraph eId="sec_2__subsec_1__para_a">
                  <num>(a)</num>
                </paragraph>
                <paragraph eId="sec_2__subsec_1__para_b">
                  <num>(b)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_2__subsec_2">
                <num>(2)</num>
              </subsection>
            </section>
        """)).root

    def test_initial(self):
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1", 8, 9,
                             element=self.doc.xpath('.//*[@eId="sec_1"]')[0],
                             eId="sec_1"))
        ], self.resolve_references_str("Section 1", self.doc))

    def test_initial_no_match(self):
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("3", 8, 9, None, ProvisionRef("(1)", 9, 12))
            )
        ], self.resolve_references_str("Section 3(1)", self.doc))

    def test_nested(self):
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef(
                    "1", 8, 9, None,
                    ProvisionRef(
                        "(1)", 9, 12,
                        element=self.doc.xpath('.//*[@eId="sec_1__subsec_1"]')[0],
                        eId="sec_1__subsec_1"
                    ),
                    element=self.doc.xpath('.//*[@eId="sec_1"]')[0],
                    eId="sec_1",
                )
            )
        ], self.resolve_references_str("Section 1(1)", self.doc))

        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef(
                    "2", 8, 9, None,
                    ProvisionRef(
                        "(1)", 9, 12, None,
                        ProvisionRef(
                            "(a)", 12, 15,
                            element=self.doc.xpath('.//*[@eId="sec_2__subsec_1__para_a"]')[0],
                            eId="sec_2__subsec_1__para_a"
                        ),
                        element=self.doc.xpath('.//*[@eId="sec_2__subsec_1"]')[0],
                        eId="sec_2__subsec_1",
                    ),
                    element=self.doc.xpath('.//*[@eId="sec_2"]')[0],
                    eId="sec_2",
                )
            )
        ], self.resolve_references_str("Section 2(1)(a)", self.doc))

    def test_nested_truncated(self):
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef(
                    "2", 8, 9, None,
                    ProvisionRef(
                        "(1)", 9, 12, None,
                        ProvisionRef("(d)", 12, 15),
                        element=self.doc.xpath('.//*[@eId="sec_2__subsec_1"]')[0],
                        eId="sec_2__subsec_1",
                    ),
                    element=self.doc.xpath('.//*[@eId="sec_2"]')[0],
                    eId="sec_2",
                )
            )
        ], self.resolve_references_str("Section 2(1)(d)", self.doc))

    def test_local(self):
        root = self.doc.xpath('.//*[@eId="sec_2"]')[0]
        self.assertEqual([
            MainProvisionRef(
                "paragraph",
                ProvisionRef(
                    "(a)", 10, 13,
                    element=self.doc.xpath('.//*[@eId="sec_2__subsec_1__para_a"]')[0],
                    eId="sec_2__subsec_1__para_a",
                ),
            ),
            MainProvisionRef(
                "subsection",
                ProvisionRef(
                    "(1)", 26, 29,
                    element=self.doc.xpath('.//*[@eId="sec_2__subsec_1"]')[0],
                    eId="sec_2__subsec_1",
                ),
            ),
        ], self.resolve_references_str("paragraph (a), subsection (1)", root))

    def test_not_outside_of(self):
        self.doc = AkomaNtosoDocument(document_fixture(xml="""
        <article eId="art_44">
          <num>44</num>
          <heading>Termination of arbitral proceedings</heading>
          <content>
            <p eId="art_44__p_1">The arbitral proceedings are terminated by the pronouncement of the decisions in substance or by an order of the arbitral tribunal in accordance with paragraph <ref href="#chp_II__sec_5__subsec_2">2</ref> of this Article.</p>
          </content>
        </article>
        <article eid="art_45">
          <num>45</num>
          <subsection eId="art_45__subsec_2">
            <num>2</num>
            <content>
              <p>subsection 2 which can be mistaken for paragraph 2</p>
            </content>
          </subsection>
          <paragraph eId="art_45__para_2">
            <num>2</num>
            <content>
              <p>paragraph 2</p>
            </content>
          </paragraph>
        </article>
        """)).root
        root = self.doc.xpath('.//*[@eId="art_44__p_1"]')[0]
        self.assertEqual([
            MainProvisionRef(
                "Paragraph",
                ProvisionRef("2", 10, 11, None))
        ], self.resolve_references_str("Paragraph 2", root))

    def test_items_as_paragraphs(self):
        self.doc = AkomaNtosoDocument(document_fixture(xml="""
        <section eId="sec_2">
          <num>2</num>
          <content>
            <blockList eId="sec_2__list_1">
              <item eId="sec_2__list_1__item_a">
                <num>(a)</num>
                <p eId="sec_2__list_1__item_a__p_1">some text</p>
                <blockList eId="sec_2__list_1__item_a__list_1">
                  <item eId="sec_2__list_1__item_a__list_1__item_i">
                    <num>(i)</num>
                    <p eId="sec_2__list_1__item_a__list_1__item_i__p_1">item (a)(i)</p>
                  </item>
                </blockList>
              </item>
              <item eId="sec_2__list_1__item_b">
                <num>(b)</num>
                <p eId="sec_2__list_1__item_b__p_1">reference to paragraph (a)(i)</p>
              </item>
            </blockList>
          </content>
        </section>
        """)).root
        root = self.doc.xpath('.//*[@eId="sec_2__list_1__item_b"]')[0]
        item_a = self.doc.xpath('.//*[@eId="sec_2__list_1__item_a"]')[0]
        item_a_i = self.doc.xpath('.//*[@eId="sec_2__list_1__item_a__list_1__item_i"]')[0]
        self.assertEqual([
            MainProvisionRef(
                'paragraph',
                ProvisionRef(
                    '(a)', 10, 13, None,
                    ProvisionRef('(i)', 13, 16, element=item_a_i, eId='sec_2__list_1__item_a__list_1__item_i'),
                    item_a,
                    'sec_2__list_1__item_a'
                )
            )
        ], self.resolve_references_str("paragraph (a)(i)", root))

    def test_roman_nums(self):
        self.doc = AkomaNtosoDocument(document_fixture(xml="""
        <section eId="sec_V">
          <num>V</num>
          <content>
            <p eId="sec_V__p_1">some text</p>
          </content>
        </section>
        <section eId="sec_VII">
          <num>VII</num>
          <content>
            <p eId="sec_VII__p_1">some text</p>
          </content>
        </section>
        """)).root
        root = self.doc.xpath('.//*[@eId="sec_V__p_1"]')[0]
        sec_v = self.doc.xpath('.//*[@eId="sec_V"]')[0]
        sec_vii = self.doc.xpath('.//*[@eId="sec_VII"]')[0]

        self.assertEqual([
            MainProvisionRef(
                'Section',
                ProvisionRef('V', 8, 9, element=sec_v, eId='sec_V')
            )
        ], self.resolve_references_str("Section V", root))

        self.assertEqual([
            MainProvisionRef(
                'Section',
                ProvisionRef('VII', 8, 11, element=sec_vii, eId='sec_VII')
            )
        ], self.resolve_references_str("Section VII", root))

    def test_schedule(self):
        self.doc = AkomaNtosoDocument(component_fixture(text="test", heading="Schedule 2")).root
        # xpath for the body element with any namespace
        root = self.doc.xpath('//*[local-name()="body"]')[0]
        att_1 = self.doc.xpath('//*[@eId="att_1"]')[0]
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("Schedule 2", 0, 10, element=att_1, eId='att_1'))
        ], self.resolve_references_str("Schedule 2", root))


class ProvisionRefsMatcherTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.finder = ProvisionRefsMatcher()
        self.frbr_uri = FrbrUri.parse("/akn/za/act/2009/1/eng@2009-01-01")
        self.target_doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        # inject the remote target document fixture
        self.finder.target_root_cache = {"/akn/za/act/2009/1": ("/akn/za/act/2009/1", self.target_doc.root)}

    def test_local_sections(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>As given in section 26, blah.</p>
                <p>As given in section 26(a), blah.</p>
                <p>As given in section 26(a)(1)(iii), blah.</p>
                <p>As given in section 26(a)(2)(iii)(bb), blah.</p>
                <p>As given in section 26(b)(b)(iii)(dd)(A), blah.</p>
                <p>As given in section 26B, blah.</p>
                <p>As given in section 26 and section 31, blah.</p>
                <p>As <i>given</i> in (we're now in a tail) section 26, blah.</p>
                <p>As given in sections 26 and 31, blah.</p>
                <p>As given in sections 26, 26B, 30 and 31, blah.</p>
                <p>As given in section 26 or 31, blah.</p>
                <p>As given in sections 26 or 31, blah.</p>
                <p>As given in sections 26, 30(1) and 31, blah.</p>
                <p>As given in sections 26, 30 (1) and 31, blah.</p>
                <p>As given in sections 26(b), 30(1) or 31, blah.</p>
                <p>As given in section 26 (b), 30 (1) or 31, blah.</p>
                <p>As <i>given</i> in (we're now in a tail) section 26, 30 and 31.</p>
                <p>under sections 26,30 or 31 of this Act, blah.</p>
                <p>As given in sections 26, 30, and 31 of this Act, blah.</p>
                <p>As given in section V and VII.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
            <section eId="sec_V">
              <num>V</num>
              <heading>Roman 5</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
            <section eId="sec_VII">
              <num>VII</num>
              <heading>Roman 7</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>As given in section <ref href="#sec_26">26</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_a">26(a)</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_a__para_1">26(a)(1)</ref>(iii), blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_a__para_2">26(a)(2)</ref>(iii)(bb), blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_b">26(b)</ref>(b)(iii)(dd)(A), blah.</p>
                <p>As given in section <ref href="#sec_26B">26B</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26">26</ref> and section <ref href="#sec_31">31</ref>, blah.</p>
                <p>As <i>given</i> in (we're now in a tail) section <ref href="#sec_26">26</ref>, blah.</p>
                <p>As given in sections <ref href="#sec_26">26</ref> and <ref href="#sec_31">31</ref>, blah.</p>
                <p>As given in sections <ref href="#sec_26">26</ref>, <ref href="#sec_26B">26B</ref>, 30 and <ref href="#sec_31">31</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26">26</ref> or <ref href="#sec_31">31</ref>, blah.</p>
                <p>As given in sections <ref href="#sec_26">26</ref> or <ref href="#sec_31">31</ref>, blah.</p>
                <p>As given in sections <ref href="#sec_26">26</ref>, 30(1) and <ref href="#sec_31">31</ref>, blah.</p>
                <p>As given in sections <ref href="#sec_26">26</ref>, 30 (1) and <ref href="#sec_31">31</ref>, blah.</p>
                <p>As given in sections <ref href="#sec_26__subsec_b">26(b)</ref>, 30(1) or <ref href="#sec_31">31</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_b">26 (b)</ref>, 30 (1) or <ref href="#sec_31">31</ref>, blah.</p>
                <p>As <i>given</i> in (we're now in a tail) section <ref href="#sec_26">26</ref>, 30 and <ref href="#sec_31">31</ref>.</p>
                <p>under sections <ref href="#sec_26">26</ref>,30 or <ref href="#sec_31">31</ref> of this Act, blah.</p>
                <p>As given in sections <ref href="#sec_26">26</ref>, 30, and <ref href="#sec_31">31</ref> of this Act, blah.</p>
                <p>As given in section <ref href="#sec_V">V</ref> and <ref href="#sec_VII">VII</ref>.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
            <section eId="sec_V">
              <num>V</num>
              <heading>Roman 5</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
            <section eId="sec_VII">
              <num>VII</num>
              <heading>Roman 7</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_local_sections_synonyms(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>As given in section 26, blah.</p>
                <p>As given in regulation 26B, blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                  <content>
                    <p>As given in paragraph (a), blah.</p>
                    <p>As given in subparagraph (1), blah.</p>
                    <p>As given in paragraph (a)(2), blah.</p>
                    <p>As given in subregulation (a)(1), blah.</p>
                  </content>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>As given in section <ref href="#sec_26">26</ref>, blah.</p>
                <p>As given in regulation <ref href="#sec_26B">26B</ref>, blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                  <content>
                    <p>As given in paragraph <ref href="#sec_26__subsec_a">(a)</ref>, blah.</p>
                    <p>As given in subparagraph <ref href="#sec_26__subsec_a__para_1">(1)</ref>, blah.</p>
                    <p>As given in paragraph <ref href="#sec_26__subsec_a__para_2">(a)(2)</ref>, blah.</p>
                    <p>As given in subregulation <ref href="#sec_26__subsec_a__para_1">(a)(1)</ref>, blah.</p>
                  </content>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_num_punct(self):
        # nums can be surrounded by () or have . or º at the end
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>As given in section 26, blah.</p>
                <p>As given in section 26(a), blah.</p>
                <p>As given in section 26(a)(1)(iii), blah.</p>
                <p>As given in section 26B, blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26Bº</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>As given in section <ref href="#sec_26">26</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_a">26(a)</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_a__para_1">26(a)(1)</ref>(iii), blah.</p>
                <p>As given in section <ref href="#sec_26B">26B</ref>, blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26Bº</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_local_ambiugous_levels(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>As given in section 26(a)(1) and (2), blah.</p>
                <p>As given in section 26(a)(1) and (b), blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>As given in section <ref href="#sec_26__subsec_a__para_1">26(a)(1)</ref> and <ref href="#sec_26__subsec_a__para_2">(2)</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_a__para_1">26(a)(1)</ref> and <ref href="#sec_26__subsec_b">(b)</ref>, blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_local_sections_afr(self):
        self.frbr_uri = FrbrUri.parse("/akn/za/act/2009/1/afr@2009-01-01")
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>Soos gegee in afdeling 26, blah.</p>
                <p>Soos gegee in afdeling 26(a), blah.</p>
                <p>Soos gegee in afdeling 26(a)(1)(iii), blah.</p>
                <p>Soos gegee in afdeling 26(a)(2)(iii)(bb), blah.</p>
                <p>Soos gegee in afdeling 26(b)(b)(iii)(dd)(A), blah.</p>
                <p>Soos gegee in afdeling 26B, blah.</p>
                <p>Soos gegee in afdeling 26 en afdeling 31, blah.</p>
                <p>Soos <i>gegee</i> in (ons is nou in 'n stert) afdeling 26, blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>Soos gegee in afdeling <ref href="#sec_26">26</ref>, blah.</p>
                <p>Soos gegee in afdeling <ref href="#sec_26__subsec_a">26(a)</ref>, blah.</p>
                <p>Soos gegee in afdeling <ref href="#sec_26__subsec_a__para_1">26(a)(1)</ref>(iii), blah.</p>
                <p>Soos gegee in afdeling <ref href="#sec_26__subsec_a__para_2">26(a)(2)</ref>(iii)(bb), blah.</p>
                <p>Soos gegee in afdeling <ref href="#sec_26__subsec_b">26(b)</ref>(b)(iii)(dd)(A), blah.</p>
                <p>Soos gegee in afdeling <ref href="#sec_26B">26B</ref>, blah.</p>
                <p>Soos gegee in afdeling <ref href="#sec_26">26</ref> en afdeling <ref href="#sec_31">31</ref>, blah.</p>
                <p>Soos <i>gegee</i> in (ons is nou in 'n stert) afdeling <ref href="#sec_26">26</ref>, blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_local_sections_fra(self):
        self.frbr_uri = FrbrUri.parse("/akn/za/act/2009/1/fra@2009-01-01")
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <article eId="art_7">
              <num>7.</num>
              <heading>Article 7</heading>
              <content>
                <p>la période de validité des titres visés à l’article 8 sont</p>
              </content>
            </article>
            <article eId="art_8">
              <num>8.</num>
              <heading>Article 8</heading>
              <subsection eId="art_8__subsec_a">
                <num>(a)</num>
                <paragraph eId="art_8__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="art_8__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="art_8__subsec_b">
                <num>(b)</num>
              </subsection>
            </article>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <article eId="art_7">
              <num>7.</num>
              <heading>Article 7</heading>
              <content>
                <p>la période de validité des titres visés à l’article <ref href="#art_8">8</ref> sont</p>
              </content>
            </article>
            <article eId="art_8">
              <num>8.</num>
              <heading>Article 8</heading>
              <subsection eId="art_8__subsec_a">
                <num>(a)</num>
                <paragraph eId="art_8__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="art_8__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="art_8__subsec_b">
                <num>(b)</num>
              </subsection>
            </article>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_local_relative(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_1">
              <num>1.</num>
              <heading>Section 1</heading>
              <subsection eId="sec_1__subsec_1">
                <num>(1)</num>
              </subsection>
              <subsection eId="sec_1__subsec_2">
                <num>(2)</num>
              </subsection>
              <subsection eId="sec_1__subsec_3">
                <num>(3)</num>
                <paragraph eId="sec_1__subsec_3__para_a">
                  <num>(a)</num>
                </paragraph>
                <paragraph eId="sec_1__subsec_3__para_b">
                  <num>(b)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_1__subsec_4">
                <num>(4)</num>
                <content>
                  <p>For the purposes of subsection (1)(b) of section 2 the intention is that</p>
                  <p>For the purposes of sub section (3)(b) of section 2 the intention is that</p>
                  <p>The particulars of subsection (3)(b) of section 2 and paragraph (a) of subsection (3) are</p>
                  <p>referred to in sub-section (1), (2) or (3)(b), to the extent that...</p>
                </content>
              </subsection>
            </section>
            <section eId="sec_2">
              <num>2.</num>
              <subsection eId="sec_2__subsec_1">
                <num>(1)</num>
              </subsection>
              <subsection eId="sec_2__subsec_2">
                <num>(2)</num>
              </subsection>
              <subsection eId="sec_2__subsec_3">
                <num>(3)</num>
                <paragraph eId="sec_2__subsec_3__para_a">
                  <num>(a)</num>
                </paragraph>
                <paragraph eId="sec_2__subsec_3__para_b">
                  <num>(b)</num>
                </paragraph>
              </subsection>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_1">
              <num>1.</num>
              <heading>Section 1</heading>
              <subsection eId="sec_1__subsec_1">
                <num>(1)</num>
              </subsection>
              <subsection eId="sec_1__subsec_2">
                <num>(2)</num>
              </subsection>
              <subsection eId="sec_1__subsec_3">
                <num>(3)</num>
                <paragraph eId="sec_1__subsec_3__para_a">
                  <num>(a)</num>
                </paragraph>
                <paragraph eId="sec_1__subsec_3__para_b">
                  <num>(b)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_1__subsec_4">
                <num>(4)</num>
                <content>
                  <p>For the purposes of subsection <ref href="#sec_2__subsec_1">(1)</ref>(b) of section <ref href="#sec_2">2</ref> the intention is that</p>
                  <p>For the purposes of sub section <ref href="#sec_2__subsec_3__para_b">(3)(b)</ref> of section <ref href="#sec_2">2</ref> the intention is that</p>
                  <p>The particulars of subsection <ref href="#sec_2__subsec_3__para_b">(3)(b)</ref> of section <ref href="#sec_2">2</ref> and paragraph <ref href="#sec_1__subsec_3__para_a">(a)</ref> of subsection <ref href="#sec_1__subsec_3">(3)</ref> are</p>
                  <p>referred to in sub-section <ref href="#sec_1__subsec_1">(1)</ref>, <ref href="#sec_1__subsec_2">(2)</ref> or <ref href="#sec_1__subsec_3__para_b">(3)(b)</ref>, to the extent that...</p>
                </content>
              </subsection>
            </section>
            <section eId="sec_2">
              <num>2.</num>
              <subsection eId="sec_2__subsec_1">
                <num>(1)</num>
              </subsection>
              <subsection eId="sec_2__subsec_2">
                <num>(2)</num>
              </subsection>
              <subsection eId="sec_2__subsec_3">
                <num>(3)</num>
                <paragraph eId="sec_2__subsec_3__para_a">
                  <num>(a)</num>
                </paragraph>
                <paragraph eId="sec_2__subsec_3__para_b">
                  <num>(b)</num>
                </paragraph>
              </subsection>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_local_breadth_first_search(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_5">
              <num>5.</num>
              <heading>Section 5</heading>
              <subsection eId="sec_5__subsec_3">
                <num>(3)</num>
                <paragraph eId="sec_5__subsec_3__para_b">
                  <num>(b)</num>
                  <subparagraph eId="sec_5__subsec_3__para_b__subpara_i">
                    <num>(i)</num>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_i__subpara_aa">
                      <num>(aa)</num>
                    </subparagraph>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_i__subpara_ee">
                      <num>(ee)</num>
                      <subparagraph eId="sec_5__subsec_3__para_b__subpara_i__subpara_ee__subpara_iii">
                        <num>(iii)</num>
                      </subparagraph>
                    </subparagraph>
                  </subparagraph>
                  <subparagraph eId="sec_5__subsec_3__para_b__subpara_ii">
                    <num>(ii)</num>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_ii__subpara_aa">
                      <num>(aa)</num>
                    </subparagraph>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_ii__subpara_bb">
                      <num>(bb)</num>
                    </subparagraph>
                  </subparagraph>
                  <subparagraph eId="sec_5__subsec_3__para_b__subpara_iii">
                    <num>(iii)</num>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_iii__subpara_aa">
                      <num>(aa)</num>
                    </subparagraph>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_iii__subpara_bb">
                      <num>(bb)</num>
                    </subparagraph>
                  </subparagraph>
                  <subparagraph eId="sec_5__subsec_3__para_b__subpara_iv">
                    <num>(iv)</num>
                    <content>
                      <p>for the purposes of subparagraph (iii)(aa), something</p>
                    </content>
                  </subparagraph>
                </paragraph>
              </subsection>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_5">
              <num>5.</num>
              <heading>Section 5</heading>
              <subsection eId="sec_5__subsec_3">
                <num>(3)</num>
                <paragraph eId="sec_5__subsec_3__para_b">
                  <num>(b)</num>
                  <subparagraph eId="sec_5__subsec_3__para_b__subpara_i">
                    <num>(i)</num>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_i__subpara_aa">
                      <num>(aa)</num>
                    </subparagraph>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_i__subpara_ee">
                      <num>(ee)</num>
                      <subparagraph eId="sec_5__subsec_3__para_b__subpara_i__subpara_ee__subpara_iii">
                        <num>(iii)</num>
                      </subparagraph>
                    </subparagraph>
                  </subparagraph>
                  <subparagraph eId="sec_5__subsec_3__para_b__subpara_ii">
                    <num>(ii)</num>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_ii__subpara_aa">
                      <num>(aa)</num>
                    </subparagraph>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_ii__subpara_bb">
                      <num>(bb)</num>
                    </subparagraph>
                  </subparagraph>
                  <subparagraph eId="sec_5__subsec_3__para_b__subpara_iii">
                    <num>(iii)</num>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_iii__subpara_aa">
                      <num>(aa)</num>
                    </subparagraph>
                    <subparagraph eId="sec_5__subsec_3__para_b__subpara_iii__subpara_bb">
                      <num>(bb)</num>
                    </subparagraph>
                  </subparagraph>
                  <subparagraph eId="sec_5__subsec_3__para_b__subpara_iv">
                    <num>(iv)</num>
                    <content>
                      <p>for the purposes of subparagraph <ref href="#sec_5__subsec_3__para_b__subpara_iii__subpara_aa">(iii)(aa)</ref>, something</p>
                    </content>
                  </subparagraph>
                </paragraph>
              </subsection>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_remote_sections(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section 26 of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>.</p>
                <p>As <b>given</b> in section 26(a), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>As given in section 26(a)(1)(iii), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26(a)(2)(iii)(bb) thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26(b)(b)(iii)(dd)(A), thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <i>given</i> a tail section 31, thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <i>given</i> a tail section 31, of that act.</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section <ref href="/akn/za/act/2009/1/~sec_26">26</ref> of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>.</p>
                <p>As <b>given</b> in section <ref href="/akn/za/act/2009/1/~sec_26__subsec_a">26(a)</ref>, of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>As given in section <ref href="/akn/za/act/2009/1/~sec_26__subsec_a__para_1">26(a)(1)</ref>(iii), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section <ref href="/akn/za/act/2009/1/~sec_26__subsec_a__para_2">26(a)(2)</ref>(iii)(bb) thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section <ref href="/akn/za/act/2009/1/~sec_26__subsec_b">26(b)</ref>(b)(iii)(dd)(A), thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <i>given</i> a tail section <ref href="/akn/za/act/2009/1/~sec_31">31</ref>, thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <i>given</i> a tail section <ref href="/akn/za/act/2009/1/~sec_31">31</ref>, of that act.</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_remote_sections_afr(self):
        self.frbr_uri = FrbrUri.parse("/akn/za/act/2009/1/afr@2009-01-01")
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>Soos gegee in afdeling 26 van <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref>.</p>
                <p>Soos <b>gegee</b> in afdeling 26(a), van <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> blah.</p>
                <p>Soos gegee in afdeling 26(a)(1)(iii), van <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> blah.</p>
                <p>Aangaande <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> en afdeling 26(a)(2)(iii)(bb) daarvan.</p>
                <p>Aangaande <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> en afdeling 26(b)(b)(iii)(dd)(A), daarvan.</p>
                <p>Aangaande <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> en <i>gegee</i> 'n stert afdeling 31, daarvan.</p>
                <p>Aangaande <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> en <i>gegee</i> 'n stert afdeling 31, van daardie wet.</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>Soos gegee in afdeling <ref href="/akn/za/act/2009/1/~sec_26">26</ref> van <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref>.</p>
                <p>Soos <b>gegee</b> in afdeling <ref href="/akn/za/act/2009/1/~sec_26__subsec_a">26(a)</ref>, van <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> blah.</p>
                <p>Soos gegee in afdeling <ref href="/akn/za/act/2009/1/~sec_26__subsec_a__para_1">26(a)(1)</ref>(iii), van <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> blah.</p>
                <p>Aangaande <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> en afdeling <ref href="/akn/za/act/2009/1/~sec_26__subsec_a__para_2">26(a)(2)</ref>(iii)(bb) daarvan.</p>
                <p>Aangaande <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> en afdeling <ref href="/akn/za/act/2009/1/~sec_26__subsec_b">26(b)</ref>(b)(iii)(dd)(A), daarvan.</p>
                <p>Aangaande <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> en <i>gegee</i> 'n stert afdeling <ref href="/akn/za/act/2009/1/~sec_31">31</ref>, daarvan.</p>
                <p>Aangaande <ref href="/akn/za/act/2009/1">Wet 1 van 2009</ref> en <i>gegee</i> 'n stert afdeling <ref href="/akn/za/act/2009/1/~sec_31">31</ref>, van daardie wet.</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_remote_sections_multiple(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26(b)(b)(iii)(dd)(A) and section 31(a) thereof.</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section <ref href="/akn/za/act/2009/1/~sec_26__subsec_b">26(b)</ref>(b)(iii)(dd)(A) and section <ref href="/akn/za/act/2009/1/~sec_31">31</ref>(a) thereof.</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_remote_sections_multiple_same_name(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section 26 and section 26(a) of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>.</p>
                <p>As <b>given</b> in section 26(a) and section 31(c), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26(a)(2)(iii)(bb), and section 31 thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> <b>and</b> section 26(b)(b)(iii)(dd)(A) and section 31(a), thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26(b)(b)(iii)(dd)(A) and section 31(a) thereof.</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section <ref href="/akn/za/act/2009/1/~sec_26">26</ref> and section <ref href="/akn/za/act/2009/1/~sec_26__subsec_a">26(a)</ref> of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>.</p>
                <p>As <b>given</b> in section <ref href="/akn/za/act/2009/1/~sec_26__subsec_a">26(a)</ref> and section <ref href="/akn/za/act/2009/1/~sec_31">31</ref>(c), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section <ref href="/akn/za/act/2009/1/~sec_26__subsec_a__para_2">26(a)(2)</ref>(iii)(bb), and section <ref href="/akn/za/act/2009/1/~sec_31">31</ref> thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> <b>and</b> section <ref href="/akn/za/act/2009/1/~sec_26__subsec_b">26(b)</ref>(b)(iii)(dd)(A) and section <ref href="/akn/za/act/2009/1/~sec_31">31</ref>(a), thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section <ref href="/akn/za/act/2009/1/~sec_26__subsec_b">26(b)</ref>(b)(iii)(dd)(A) and section <ref href="/akn/za/act/2009/1/~sec_31">31</ref>(a) thereof.</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_remote_term(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_1">
              <num>1.</num>
              <heading>Section 1</heading>
              <subsection eId="sec_1__subsec_1">
                <num>(1)</num>
                <content>
                  <p refersTo="#term-the_Act">“<def refersTo="#term-the_Act">the Act</def>” means the Civil Union Act, 2006 (<ref href="/akn/za/act/2009/1">Act No. 1 of 2009</ref>).</p>
                </content>
              </subsection>
              <subsection eId="sec_1__subsec_4">
                <num>(4)</num>
                <content>
                  <p>Referring to section 26(a) of <term refersTo="#term-the_Act">the Act</term>.</p>
                </content>
              </subsection>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_1">
              <num>1.</num>
              <heading>Section 1</heading>
              <subsection eId="sec_1__subsec_1">
                <num>(1)</num>
                <content>
                  <p refersTo="#term-the_Act">“<def refersTo="#term-the_Act">the Act</def>” means the Civil Union Act, 2006 (<ref href="/akn/za/act/2009/1">Act No. 1 of 2009</ref>).</p>
                </content>
              </subsection>
              <subsection eId="sec_1__subsec_4">
                <num>(4)</num>
                <content>
                  <p>Referring to section <ref href="/akn/za/act/2009/1/~sec_26__subsec_a">26(a)</ref> of <term refersTo="#term-the_Act">the Act</term>.</p>
                </content>
              </subsection>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_remote_of_the_act(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section 26 of the Act.</p>
                <p>As given in section 26 of the act.</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section <ref href="/akn/za/act/2009/1/~sec_26">26</ref> of the Act.</p>
                <p>As given in section <ref href="/akn/za/act/2009/1/~sec_26">26</ref> of the act.</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        with patch.object(self.finder, 'find_parent_document_target') as mock:
            mock.return_value = ("/akn/za/act/2009/1", self.target_doc.root)
            self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_section_invalid(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
          <section eId="sec_7">
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
              <p>As given in section 26 of Cap. C38, blah.</p>
              <p>As given in section 26 of the Criminal Code, blah.</p>
              <p>As given in sub-section 1, blah.</p>
            </content>
          </section>
          <section eId="sec_26">
            <num>26.</num>
            <heading>Important heading</heading>
            <content>
              <p>An important provision.</p>
            </content>
          </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            doc.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_section_edge(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
          <section eId="sec_1">
            <num>1.</num>
          </section>
          <section eId="sec_2">
            <num>2.</num>
          </section>
          <section eId="sec_3">
            <num>3.</num>
          </section>
          <section eId="sec_4">
            <num>4.</num>
          </section>
          <section eId="sec_5">
            <num>5.</num>
          </section>
          <section eId="sec_6">
            <num>6.</num>
          </section>
          <section eId="sec_7">
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
              <p>A person who contravenes sections 4(1), (2) and (3), 6(3) and 10(1) and (2) is guilty of an offence.</p>
              <p>Subject to sections 1(4) and (5) and 4(6), no person is guilty of an offence.</p>
              <p>A person who contravenes sections 4(1) and (2), 6(3), 10(1) and (2), 11(1), 12(1), 19(1), 19(3), 20(1), 20(2), 21(1), 22(1), 24(1), 25(3), (4) , (5) and (6) , 26(1), (2), (3) and (5), 28(1), (2) and (3) is guilty of an offence.</p>
            </content>
          </section>
          <section eId="sec_10">
            <num>10.</num>
          </section>
          <section eId="sec_11">
            <num>11.</num>
          </section>
          <section eId="sec_12">
            <num>12.</num>
          </section>
          <section eId="sec_19">
            <num>19.</num>
          </section>
          <section eId="sec_20">
            <num>20.</num>
          </section>
          <section eId="sec_21">
            <num>21.</num>
          </section>
          <section eId="sec_22">
            <num>22.</num>
          </section>
          <section eId="sec_24">
            <num>24.</num>
          </section>
          <section eId="sec_25">
            <num>25.</num>
          </section>
          <section eId="sec_26">
            <num>26.</num>
          </section>
          <section eId="sec_28">
            <num>28.</num>
          </section>
          <section eId="sec_30">
            <num>30.</num>
          </section>
          <section eId="sec_31">
            <num>31.</num>
          </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
          <section eId="sec_1">
            <num>1.</num>
          </section>
          <section eId="sec_2">
            <num>2.</num>
          </section>
          <section eId="sec_3">
            <num>3.</num>
          </section>
          <section eId="sec_4">
            <num>4.</num>
          </section>
          <section eId="sec_5">
            <num>5.</num>
          </section>
          <section eId="sec_6">
            <num>6.</num>
          </section>
          <section eId="sec_7">
            <num>7.</num>
            <heading>Active ref heading</heading>
            <content>
              <p>As given in section <ref href="#sec_26">26</ref>(1), blah.</p>
              <p>As given in section <ref href="#sec_26">26</ref> (1), blah.</p>
              <p>As given in section <ref href="#sec_26">26</ref>(1), (2) and (3), blah.</p>
              <p>As given in section <ref href="#sec_26">26</ref> (1), (2) and (3), blah.</p>
              <p>As given in sections <ref href="#sec_26">26</ref>(1), (2) and (3), blah.</p>
              <p>As given in sections <ref href="#sec_26">26</ref> (1), (2) and (3), blah.</p>
              <p>As given in section <ref href="#sec_26">26</ref> (2) and (3), blah.</p>
              <p>As given in section <ref href="#sec_26">26</ref>(2) and (3), blah.</p>
              <p>As given in sections <ref href="#sec_26">26</ref> (2) and (3), blah.</p>
              <p>As given in sections <ref href="#sec_26">26</ref>(2) and (3), blah.</p>
              <p>A person who contravenes sections <ref href="#sec_4">4</ref>(1), (2) and (3), <ref href="#sec_6">6</ref>(3) and <ref href="#sec_10">10</ref>(1) and (2) is guilty of an offence.</p>
              <p>Subject to sections <ref href="#sec_1">1</ref>(4) and (5) and <ref href="#sec_4">4</ref>(6), no person is guilty of an offence.</p>
              <p>A person who contravenes sections <ref href="#sec_4">4</ref>(1) and (2), <ref href="#sec_6">6</ref>(3), <ref href="#sec_10">10</ref>(1) and (2), <ref href="#sec_11">11</ref>(1), <ref href="#sec_12">12</ref>(1), <ref href="#sec_19">19</ref>(1), <ref href="#sec_19">19</ref>(3), <ref href="#sec_20">20</ref>(1), <ref href="#sec_20">20</ref>(2), <ref href="#sec_21">21</ref>(1), <ref href="#sec_22">22</ref>(1), <ref href="#sec_24">24</ref>(1), <ref href="#sec_25">25</ref>(3), (4) , (5) and (6) , <ref href="#sec_26">26</ref>(1), (2), (3) and (5), <ref href="#sec_28">28</ref>(1), (2) and (3) is guilty of an offence.</p>
            </content>
          </section>
          <section eId="sec_10">
            <num>10.</num>
          </section>
          <section eId="sec_11">
            <num>11.</num>
          </section>
          <section eId="sec_12">
            <num>12.</num>
          </section>
          <section eId="sec_19">
            <num>19.</num>
          </section>
          <section eId="sec_20">
            <num>20.</num>
          </section>
          <section eId="sec_21">
            <num>21.</num>
          </section>
          <section eId="sec_22">
            <num>22.</num>
          </section>
          <section eId="sec_24">
            <num>24.</num>
          </section>
          <section eId="sec_25">
            <num>25.</num>
          </section>
          <section eId="sec_26">
            <num>26.</num>
          </section>
          <section eId="sec_28">
            <num>28.</num>
          </section>
          <section eId="sec_30">
            <num>30.</num>
          </section>
          <section eId="sec_31">
            <num>31.</num>
          </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_ignore_tags(self):
        # tables and other tags should be ignored
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <subheading>As given in section 26.</subheading>
              <content>
                <crossHeading>As given in section 26.</crossHeading>
                <embeddedStructure>As given in section 26.</embeddedStructure>
                <quotedStructure>As given in section 26.</quotedStructure>
                <p>As given in section 26.</p>
                <table>
                  <tr>
                    <td><p>As given in section 26.</p></td>
                  </tr>
                </table>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <subheading>As given in section 26.</subheading>
              <content>
                <crossHeading>As given in section 26.</crossHeading>
                <embeddedStructure>As given in section 26.</embeddedStructure>
                <quotedStructure>As given in section 26.</quotedStructure>
                <p>As given in section <ref href="#sec_26">26</ref>.</p>
                <table>
                  <tr>
                    <td><p>As given in section 26.</p></td>
                  </tr>
                </table>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_schedule_num(self):
        doc = AkomaNtosoDocument(component_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>In Schedule 2</p>
                <p>In Schedule 2.</p>
                <p>In Schedule 2 and Schedule 2.</p>
                <p>In Schedule 2 to 2.</p>
                <p>In Schedules 2, 2 and 2.</p>
                <p>In Scheduled work...</p>
                <p>In the Schedule</p>
              </content>
            </section>
        """, heading="Schedule 2"))

        expected = AkomaNtosoDocument(component_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>In <ref href="#att_1">Schedule 2</ref></p>
                <p>In <ref href="#att_1">Schedule 2</ref>.</p>
                <p>In <ref href="#att_1">Schedule 2</ref> and <ref href="#att_1">Schedule 2</ref>.</p>
                <p>In <ref href="#att_1">Schedule 2</ref> to <ref href="#att_1">2</ref>.</p>
                <p>In <ref href="#att_1">Schedules 2</ref>, <ref href="#att_1">2</ref> and <ref href="#att_1">2</ref>.</p>
                <p>In Scheduled work...</p>
                <p>In the Schedule</p>
              </content>
            </section>
        """, heading="Schedule 2"))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_schedule_name(self):
        doc = AkomaNtosoDocument(component_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>In the Schedule</p>
                <p>In the Schedule.</p>
                <p>In the Schedule and the Schedule.</p>
                <p>In Scheduled work...</p>
              </content>
            </section>
        """, heading="Schedule"))

        expected = AkomaNtosoDocument(component_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Section 7</heading>
              <content>
                <p>In the <ref href="#att_1">Schedule</ref></p>
                <p>In the <ref href="#att_1">Schedule</ref>.</p>
                <p>In the <ref href="#att_1">Schedule</ref> and the <ref href="#att_1">Schedule</ref>.</p>
                <p>In Scheduled work...</p>
              </content>
            </section>
        """, heading="Schedule"))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_subparagraphs_as_items(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
        <section eId="sec_3">
          <num>3</num>
          <intro>
            <blockList eId="sec_3__intro__list_1">
              <item eId="sec_3__intro__list_1__item_i">
                <num>(i)</num>
                <p eId="sec_3__intro__list_1__item_i__p_1">item (i)</p>
              </item>
              <item eId="sec_3__intro__list_1__item_ii">
                <num>(ii)</num>
                <p eId="sec_3__intro__list_1__item_ii__p_1">ref to subparagraph (i)</p>
              </item>
            </blockList>
          </intro>
          <subparagraph eId="sec_3__subpara_i">
            <num>(i)</num>
            <content>
              <p eId="sec_3__subpara_i__p_1">subparagraph (i)</p>
            </content>
          </subparagraph>
          <subparagraph eId="sec_3__subpara_ii">
            <num>(ii)</num>
            <content>
              <p eId="sec_3__subpara_ii__p_1">subparagraph (i)</p>
            </content>
          </subparagraph>
        </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
        <section eId="sec_3">
          <num>3</num>
          <intro>
            <blockList eId="sec_3__intro__list_1">
              <item eId="sec_3__intro__list_1__item_i">
                <num>(i)</num>
                <p eId="sec_3__intro__list_1__item_i__p_1">item <ref href="#sec_3__intro__list_1__item_i">(i)</ref></p>
              </item>
              <item eId="sec_3__intro__list_1__item_ii">
                <num>(ii)</num>
                <p eId="sec_3__intro__list_1__item_ii__p_1">ref to subparagraph <ref href="#sec_3__intro__list_1__item_i">(i)</ref></p>
              </item>
            </blockList>
          </intro>
          <subparagraph eId="sec_3__subpara_i">
            <num>(i)</num>
            <content>
              <p eId="sec_3__subpara_i__p_1">subparagraph <ref href="#sec_3__subpara_i">(i)</ref></p>
            </content>
          </subparagraph>
          <subparagraph eId="sec_3__subpara_ii">
            <num>(ii)</num>
            <content>
              <p eId="sec_3__subpara_ii__p_1">subparagraph <ref href="#sec_3__subpara_i">(i)</ref></p>
            </content>
          </subparagraph>
        </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_markup_html(self):
        html = '<p>Concerning <a href="/akn/za/act/2009/1">Act 1 of 2009</a> and section 26(b) and section 31(a) thereof.</p>'
        expected = '<p>Concerning <a href="/akn/za/act/2009/1">Act 1 of 2009</a> and section <a href="/akn/za/act/2009/1/~sec_26__subsec_b">26(b)</a> and section <a href="/akn/za/act/2009/1/~sec_31">31</a>(a) thereof.</p>'

        actual = parse_html_str(html)
        self.finder.markup_html_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected,
            etree.tostring(actual, encoding='unicode')
        )

    def test_markup_html_local(self):
        html = '<p>Concerning section 26(b) of this act, and section 2 of <a href="#footnote">a footnote</a>.</p>'

        actual = parse_html_str(html)
        self.finder.markup_html_matches(self.frbr_uri, actual)
        self.assertEqual(
            html,
            etree.tostring(actual, encoding='unicode')
        )

    def test_markup_html_dont_cross_sentences(self):
        html = '<p>Section 26 of the Education Act says <b>interesting</b> things. Section 1 of <a href="/akn/za/act/2009/1">Act 1 of 2009</a> is also interesting.</p>'
        expected = '<p>Section 26 of the Education Act says <b>interesting</b> things. Section 1 of <a href="/akn/za/act/2009/1">Act 1 of 2009</a> is also interesting.</p>'

        actual = parse_html_str(html)
        self.finder.markup_html_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected,
            etree.tostring(actual, encoding='unicode')
        )

    def test_markup_html_dont_cross_sentences_backwards(self):
        html = '<p>Section 1 of <a href="/akn/za/act/2009/1">Act 1 of 2009</a> is <b>interesting</b>. The Education Act, Section 26 thereof, is also.</p>'
        expected = '<p>Section 1 of <a href="/akn/za/act/2009/1">Act 1 of 2009</a> is <b>interesting</b>. The Education Act, Section 26 thereof, is also.</p>'

        actual = parse_html_str(html)
        self.finder.markup_html_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected,
            etree.tostring(actual, encoding='unicode')
        )

    def test_markup_text(self):
        text = """According to section 26 and 26(a) of Act No. 1 of 2009."""
        self.finder.setup(self.frbr_uri, text=text)
        self.finder.citations = [
            ExtractedCitation("Act No. 1 of 2009", 37, 54, "/akn/za/act/2009/1", 0, 'of Act No. ', '.' ),
        ]
        self.finder.extract_paged_text_matches()
        self.assertEqual([
            ExtractedCitation("Act No. 1 of 2009", 37, 54, "/akn/za/act/2009/1", 0, 'of Act No. ', '.'),
            ExtractedCitation("26", 21, 23, "/akn/za/act/2009/1/~sec_26", 0, 'According to section ', ' and 26(a) of Act No. 1 of 200' ),
            ExtractedCitation("26(a)", 28, 33, "/akn/za/act/2009/1/~sec_26__subsec_a", 0, 'According to section 26 and ', ' of Act No. 1 of 2009.'),
        ], self.finder.citations)

    def test_markup_text_thereof(self):
        text = """Regarding Act No. 1 of 2009 and section 26 thereof."""
        self.finder.setup(self.frbr_uri, text=text)
        self.finder.citations = [
            ExtractedCitation("Act No. 1 of 2009", 10, 27, "/akn/za/act/2009/1", 0, 'Regarding ', ' and section' ),
        ]
        self.finder.extract_paged_text_matches()
        self.assertEqual([
            ExtractedCitation("Act No. 1 of 2009", 10, 27, "/akn/za/act/2009/1", 0, 'Regarding ', ' and section' ),
            ExtractedCitation("26", 40, 42, "/akn/za/act/2009/1/~sec_26", 0, 'Act No. 1 of 2009 and section ', ' thereof.' ),
        ], self.finder.citations)

    def test_markup_text_mixed_page_numbers(self):
        text = """Reference to Act No. 1 of 2009.\x0COn a new page section 26 of Act No. 1 of 2009.\x0CAct No. 1 of 2009."""
        self.finder.setup(self.frbr_uri, text=text)
        self.finder.citations = [
            ExtractedCitation("Act No. 1 of 2009", 21, 30, "/akn/za/act/2009/1", 0, 'of Act No. ', '.' ),
            ExtractedCitation("Act No. 1 of 2009", 0, 9, "/akn/za/act/2009/1", 2, '', '.'),
        ]
        # nothing is found because the Act references are on different pages
        self.finder.extract_paged_text_matches()
        self.assertEqual([
            ExtractedCitation("Act No. 1 of 2009", 21, 30, "/akn/za/act/2009/1", 0, 'of Act No. ', '.' ),
            ExtractedCitation("Act No. 1 of 2009", 0, 9, "/akn/za/act/2009/1", 2, '', '.'),
        ], self.finder.citations)

    def test_markup_text_newlines(self):
        text = """According to section 26\nand 26(a)\nof Act No. 1 of 2009."""
        self.finder.setup(self.frbr_uri, text=text)
        self.finder.citations = [
            ExtractedCitation("Act No. 1 of 2009", 37, 54, "/akn/za/act/2009/1", 0, 'of Act No. ', '.'),
        ]
        self.finder.extract_paged_text_matches()
        self.assertEqual([
            ExtractedCitation("Act No. 1 of 2009", 37, 54, "/akn/za/act/2009/1", 0, 'of Act No. ', '.'),
            ExtractedCitation("26", 21, 23, "/akn/za/act/2009/1/~sec_26", 0, 'According to section ', '\nand 26(a)\nof Act No. 1 of 200' ),
            ExtractedCitation("26(a)", 28, 33, "/akn/za/act/2009/1/~sec_26__subsec_a", 0, 'According to section 26\nand ', '\nof Act No. 1 of 2009.'),
        ], self.finder.citations)

    def test_markup_text_no_dups(self):
        text = """Interpretation of section 26 of Act 1 of 2009 and Section 26(a) of Act 1 of 2009 deals with..."""
        self.finder.setup(self.frbr_uri, text=text)
        self.finder.citations = [
            ExtractedCitation("the Act", 32, 45, "/akn/za/act/2009/1", 0, ' of ', ' and '),
            ExtractedCitation("the Act", 68, 81, "/akn/za/act/2009/1", 0, ' of ', ' deals '),
        ]
        self.finder.extract_paged_text_matches()
        self.assertEqual([
            ExtractedCitation("the Act", 32, 45, "/akn/za/act/2009/1", 0, ' of ', ' and '),
            ExtractedCitation("the Act", 68, 81, "/akn/za/act/2009/1", 0, ' of ', ' deals '),
            ExtractedCitation('26(a)', 58, 63, '/akn/za/act/2009/1/~sec_26__subsec_a', 0,
                              ' of Act 1 of 2009 and Section ', ' of Act 1 of 2009 deals with..'),
            ExtractedCitation('26', 26, 28, '/akn/za/act/2009/1/~sec_26', 0,
                              'Interpretation of section ', ' of Act 1 of 2009 and Section '),
        ], self.finder.citations)

    def test_markup_text_dont_cross_sentences(self):
        text = 'Section 26 of the Education Act says interesting things. Section 1 of Act 1 of 2009 is also interesting.'
        self.finder.setup(self.frbr_uri, text=text)
        self.finder.citations = [
            ExtractedCitation("Act No. 1 of 2009", 87, 95, "/akn/za/act/2009/1", 0, 'of Act No. ', '.' ),
        ]
        self.finder.extract_paged_text_matches()
        self.assertEqual([
            ExtractedCitation("Act No. 1 of 2009", 87, 95, "/akn/za/act/2009/1", 0, 'of Act No. ', '.' ),
        ], self.finder.citations)

    def test_markup_text_dont_cross_sentences_backwards(self):
        text = 'Section 1 of Act 1 of 2009 is interesting. The Education Act, Section 26 thereof, is also.'
        self.finder.setup(self.frbr_uri, text=text)
        self.finder.citations = [
            ExtractedCitation("Act No. 1 of 2009", 30, 38, "/akn/za/act/2009/1", 0, 'of Act No. ', '.' ),
        ]
        self.finder.extract_paged_text_matches()
        self.assertEqual([
            ExtractedCitation("Act No. 1 of 2009", 30, 38, "/akn/za/act/2009/1", 0, 'of Act No. ', '.' ),
        ], self.finder.citations)
