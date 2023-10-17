import unittest.util

from django.test import TestCase
from lxml import etree

from cobalt import AkomaNtosoDocument, FrbrUri

from indigo.analysis.refs.provisions import ProvisionRefsResolver, ProvisionRef, ProvisionRefsMatcher, parse_provision_refs, MainProvisionRef
from indigo_api.tests.fixtures import document_fixture


unittest.util._MAX_LENGTH = 999999999


class ProvisionRefsResolverTestCase(TestCase):
    maxDiff = None

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
        ], self.resolver.resolve_references_str("Section 1", self.doc))

    def test_initial_no_match(self):
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("3", 8, 9, None, ProvisionRef("(1)", 9, 12))
            )
        ], self.resolver.resolve_references_str("Section 3(1)", self.doc))

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
        ], self.resolver.resolve_references_str("Section 1(1)", self.doc))

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
        ], self.resolver.resolve_references_str("Section 2(1)(a)", self.doc))

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
        ], self.resolver.resolve_references_str("Section 2(1)(d)", self.doc))

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
        ], self.resolver.resolve_references_str("paragraph (a), subsection (1)", root))


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
        self.finder.target_root_cache = {"/akn/za/act/2009/1": self.target_doc.root}

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

    def test_local_sections_af(self):
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

    @unittest.expectedFailure
    def test_local_relative(self):
        # TODO: this doesn't pass yet, because we don't do local relative resolution correctly
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
                  <p>referred to in sub-section (1), (2) or (3)(b), to the extent that...</p>
                  <p>For the purposes of subsection (1)(b) of section 2 the intention is that</p>
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
                  <p>referred to in sub-section <ref href="#sec_1__subsec_1">(1)</ref>, <ref href="#sec_1__subsec_2">(2)</ref> or <ref href="#sec_1__subsec_3__para_b">(3)(b)</ref>, to the extent that...</p>
                  <p>For the purposes of subsection <ref href="#sec_2__subsec_1__para_b">(1)(b)</ref> of section <ref href="#sec_2">2</ref> the intention is that</p>
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
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_remote_sections_af(self):
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


class ProvisionRefsGrammarTest(TestCase):
    maxDiff = None

    def test_single(self):
        result = parse_provision_refs("Section 1")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1", 8, 9)
            )
        ], result['references'])

        result = parse_provision_refs("paragraph (a)")
        self.assertEqual([
            MainProvisionRef(
                "paragraph",
                ProvisionRef("(a)", 10, 13)
            )
        ], result['references'])

    def test_multiple_main_numbers(self):
        result = parse_provision_refs("Section 1, 32 and 33")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1", 8, 9)
            ),
            MainProvisionRef(
                "Section",
                ProvisionRef("32", 11, 13)
            ),
            MainProvisionRef(
                "Section",
                ProvisionRef("33", 18, 20)
            )
        ], result['references'])

        result = parse_provision_refs("paragraph (a) and subparagraph (c)")
        self.assertEqual([
            MainProvisionRef(
                "paragraph",
                ProvisionRef("(a)", 10, 13)
            ),
            MainProvisionRef(
                "subparagraph",
                ProvisionRef("(c)", 31, 34)
            )
        ], result['references'])

    def test_multiple_main(self):
        result = parse_provision_refs("Section 1 and section 2, section 3 and chapter 4")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1", 8, 9)
            ),
            MainProvisionRef(
                "section",
                ProvisionRef("2", 22, 23)
            ),
            MainProvisionRef(
                "section",
                ProvisionRef("3", 33, 34)
            ),
            MainProvisionRef(
                "chapter",
                ProvisionRef("4", 47, 48)
            )
        ], result['references'])

    def test_mixed(self):
        result = parse_provision_refs("Section 1.2(1)(a),(c) to (e), (f)(ii) and (2), and (3)(g),(h) and section 32(a)")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1.2", 8, 11, None,
                    ProvisionRef("(1)", 11, 14, None,
                        ProvisionRef("(a)", 14, 17)
                    ),
                ), [
                    ProvisionRef("(c)", 18, 21, "and_or"),
                    ProvisionRef("(e)", 25, 28, "range"),
                    ProvisionRef("(f)", 30, 33, "and_or",
                        ProvisionRef("(ii)", 33, 37),
                    ),
                    ProvisionRef("(2)", 42, 45, "and_or"),
                    ProvisionRef("(3)", 51, 54, "and_or",
                        ProvisionRef("(g)", 54, 57),
                    ),
                    ProvisionRef("(h)", 58, 61, "and_or"),
                ]
            ),
            MainProvisionRef(
                "section",
                ProvisionRef("32", 74, 76, None,
                    ProvisionRef("(a)", 76, 79),
                ),
            )
        ], result['references'])
        self.assertIsNone(result["target"])

    def test_mixed_af(self):
        result = parse_provision_refs("Afdeling 1.2(1)(a),(c) tot (e), (f)(ii) en (2), en (3)(g),(h) en afdelings 32(a)")
        self.assertEqual([
            MainProvisionRef(
                "Afdeling",
                ProvisionRef("1.2", 9, 12, None,
                    ProvisionRef("(1)", 12, 15, None,
                        ProvisionRef("(a)", 15, 18)
                    ),
                ), [
                    ProvisionRef("(c)", 19, 22, "and_or"),
                    ProvisionRef("(e)", 27, 30, "range"),
                    ProvisionRef("(f)", 32, 35, "and_or",
                        ProvisionRef("(ii)", 35, 39)),
                    ProvisionRef("(2)", 43, 46, "and_or"),
                    ProvisionRef("(3)", 51, 54, "and_or",
                        ProvisionRef("(g)", 54, 57)),
                    ProvisionRef("(h)", 58, 61, "and_or"),
                ]
            ),
            MainProvisionRef(
                "afdelings",
                ProvisionRef("32", 75, 77, None,
                    ProvisionRef("(a)", 77, 80),
                ),
            )
        ], result['references'])
        self.assertIsNone(result["target"])

    def test_multiple_mains(self):
        result = parse_provision_refs("Section 2(1), section 3(b) and section 32(a)")
        self.assertEqual([
            MainProvisionRef('Section', ProvisionRef('2', 8, 9, None, ProvisionRef('(1)', 9, 12))),
            MainProvisionRef('section', ProvisionRef('3', 22, 23, None, ProvisionRef('(b)', 23, 26))),
            MainProvisionRef('section', ProvisionRef('32', 39, 41, None, ProvisionRef('(a)', 41, 44)))
        ], result['references'])
        self.assertIsNone(result["target"])

        result = parse_provision_refs("Sections 26 and 31")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('26', 9, 11)),
            MainProvisionRef('Sections', ProvisionRef('31', 16, 18)),
        ], result['references'])
        self.assertIsNone(result["target"])

        result = parse_provision_refs("Sections 26 and 31.")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('26', 9, 11)),
            MainProvisionRef('Sections', ProvisionRef('31', 16, 18)),
        ], result['references'])
        self.assertIsNone(result["target"])

    def test_multiple_mains_range(self):
        result = parse_provision_refs("Sections 26 to 31")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('26', 9, 11)),
            MainProvisionRef('Sections', ProvisionRef('31', 15, 17)),
        ], result['references'])
        self.assertIsNone(result["target"])

        result = parse_provision_refs("Sections 26, 27 and 28 to 31")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('26', 9, 11)),
            MainProvisionRef('Sections', ProvisionRef('27', 13, 15)),
            MainProvisionRef('Sections', ProvisionRef('28', 20, 22)),
            MainProvisionRef('Sections', ProvisionRef('31', 26, 28)),
        ], result['references'])
        self.assertIsNone(result["target"])

    def test_multiple_mains_target(self):
        result = parse_provision_refs("Sections 2(1), section 3(b) and section 32(a) of another Act")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('2', 9, 10, None, ProvisionRef('(1)', 10, 13))),
            MainProvisionRef('section', ProvisionRef('3', 23, 24, None, ProvisionRef('(b)', 24, 27))),
            MainProvisionRef('section', ProvisionRef('32', 40, 42, None, ProvisionRef('(a)', 42, 45)))
        ], result['references'])
        self.assertEqual("of", result["target"])

    def test_target(self):
        result = parse_provision_refs("Section 2 of this Act")
        self.assertEqual("this", result["target"])

        result = parse_provision_refs("Section 2, of this Act")
        self.assertEqual("this", result["target"])

        result = parse_provision_refs("Section 2 thereof")
        self.assertEqual("thereof", result["target"])

        result = parse_provision_refs("Section 2, thereof and some")
        self.assertEqual("thereof", result["target"])

        result = parse_provision_refs("Section 2 of the Act")
        self.assertEqual("of", result["target"])

        result = parse_provision_refs("Section 2, of the Act with junk")
        self.assertEqual("of", result["target"])

    def test_target_af(self):
        result = parse_provision_refs("Afdeling 2 van hierdie Wet")
        self.assertEqual("this", result["target"])

        result = parse_provision_refs("Afdeling 2 daarvan")
        self.assertEqual("thereof", result["target"])

        result = parse_provision_refs("Afdeling 2 van die Wet met kak")
        self.assertEqual("of", result["target"])
