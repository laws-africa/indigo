import unittest.util

from django.test import TestCase
from lxml import etree

from cobalt import AkomaNtosoDocument, FrbrUri

from indigo.analysis.refs.provisions import ProvisionRefsResolver, ProvisionRef, ProvisionRefsMatcher, parse_refs, MainProvisionRef
from indigo_api.tests.fixtures import document_fixture


unittest.util._MAX_LENGTH = 999999999


class ProvisionRefsResolverTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.resolver = ProvisionRefsResolver()
        self.doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_1">
              <num>1.</num>
              <subsection eId="sec_1__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_1__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_1__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_1__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_2">
              <num>2.</num>
              <subsection eId="sec_2__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_2__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_2__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_2__subsec_b">
                <num>(b)</num>
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
                ProvisionRef("3", 8, 9, None, ProvisionRef("(a)", 9, 12))
            )
        ], self.resolver.resolve_references_str("Section 3(a)", self.doc))

    def test_nested(self):
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef(
                    "1", 8, 9, None,
                    ProvisionRef(
                        "(a)", 9, 12,
                        element=self.doc.xpath('.//*[@eId="sec_1__subsec_a"]')[0],
                        eId="sec_1__subsec_a"
                    ),
                    element=self.doc.xpath('.//*[@eId="sec_1"]')[0],
                    eId="sec_1",
                )
            )
        ], self.resolver.resolve_references_str("Section 1(a)", self.doc))

        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef(
                    "2", 8, 9, None,
                    ProvisionRef(
                        "(a)", 9, 12, None,
                        ProvisionRef(
                            "(2)", 12, 15,
                            element=self.doc.xpath('.//*[@eId="sec_2__subsec_a__para_2"]')[0],
                            eId="sec_2__subsec_a__para_2"
                        ),
                        element=self.doc.xpath('.//*[@eId="sec_2__subsec_a"]')[0],
                        eId="sec_2__subsec_a",
                    ),
                    element=self.doc.xpath('.//*[@eId="sec_2"]')[0],
                    eId="sec_2",
                )
            )
        ], self.resolver.resolve_references_str("Section 2(a)(2)", self.doc))

    def test_nested_truncated(self):
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef(
                    "2", 8, 9, None,
                    ProvisionRef(
                        "(a)", 9, 12, None,
                        ProvisionRef("(8)", 12, 15),
                        element=self.doc.xpath('.//*[@eId="sec_2__subsec_a"]')[0],
                        eId="sec_2__subsec_a",
                    ),
                    element=self.doc.xpath('.//*[@eId="sec_2"]')[0],
                    eId="sec_2",
                )
            )
        ], self.resolver.resolve_references_str("Section 2(a)(8)", self.doc))


class ProvisionRefsMatechTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.finder = ProvisionRefsMatcher()
        self.frbr_uri = FrbrUri.parse("/akn/za/act/2009/1/eng@2009-01-01")

    def test_local_sections(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section 26, blah.</p>
                <p>As given in section 26(a), blah.</p>
                <p>As given in section 26(a)(1)(iii), blah.</p>
                <p>As given in section 26(a)(2)(iii)(bb), blah.</p>
                <p>As given in section 26(b)(b)(iii)(dd)(A), blah.</p>
                <p>As given in section 26B, blah.</p>
                <p>As given in section 26 and section 31, blah.</p>
                <p>As <i>given</i> in (we're now in a tail) section 26, blah.</p>
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
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section <ref href="#sec_26">26</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_a">26(a)</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_a__para_1">26(a)(1)</ref>(iii), blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_a__para_2">26(a)(2)</ref>(iii)(bb), blah.</p>
                <p>As given in section <ref href="#sec_26__subsec_b">26(b)</ref>(b)(iii)(dd)(A), blah.</p>
                <p>As given in section <ref href="#sec_26B">26B</ref>, blah.</p>
                <p>As given in section <ref href="#sec_26">26</ref> and section <ref href="#sec_31">31</ref>, blah.</p>
                <p>As <i>given</i> in (we're now in a tail) section <ref href="#sec_26">26</ref>, blah.</p>
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

        target_doc = AkomaNtosoDocument(document_fixture(xml="""
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
        self.finder.target_root_cache = {"/akn/za/act/2009/1": target_doc.root}

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

        target_doc = AkomaNtosoDocument(document_fixture(xml="""
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
        self.finder.target_root_cache = {"/akn/za/act/2009/1": target_doc.root}

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )


class RefsGrammarTest(TestCase):
    maxDiff = None

    def test_single(self):
        result = parse_refs("Section 1")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1", 8, 9)
            )
        ], result['references'])

    def test_mixed(self):
        result = parse_refs("Section 1.2(1)(a),(c) to (e), (f)(ii) and (2), and (3)(g),(h) and section 32(a)")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1.2", 8, 11, None,
                    ProvisionRef("(1)", 11, 14, None,
                        ProvisionRef("(a)", 14, 17)
                    ),
                ),
                [
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

    def test_multiple_mains(self):
        result = parse_refs("Section 2(1), section 3(b) and section 32(a)")
        self.assertEqual([
            MainProvisionRef('Section', ProvisionRef('2', 8, 9, None, ProvisionRef('(1)', 9, 12))),
            MainProvisionRef('section', ProvisionRef('3', 22, 23, None, ProvisionRef('(b)', 23, 26))),
            MainProvisionRef('section', ProvisionRef('32', 39, 41, None, ProvisionRef('(a)', 41, 44)))
        ], result['references'])
        self.assertIsNone(result["target"])

    def test_multiple_mains_target(self):
        result = parse_refs("Section 2(1), section 3(b) and section 32(a) of another Act")
        self.assertEqual([
            MainProvisionRef('Section', ProvisionRef('2', 8, 9, None, ProvisionRef('(1)', 9, 12))),
            MainProvisionRef('section', ProvisionRef('3', 22, 23, None, ProvisionRef('(b)', 23, 26))),
            MainProvisionRef('section', ProvisionRef('32', 39, 41, None, ProvisionRef('(a)', 41, 44)))
        ], result['references'])
        self.assertEqual("of", result["target"])

    def test_target(self):
        result = parse_refs("Section 2 of this Act")
        self.assertEqual("this", result["target"])

        result = parse_refs("Section 2, of this Act")
        self.assertEqual("this", result["target"])

        result = parse_refs("Section 2 thereof")
        self.assertEqual("thereof", result["target"])

        result = parse_refs("Section 2, thereof and some")
        self.assertEqual("thereof", result["target"])

        result = parse_refs("Section 2 of the Act")
        self.assertEqual("of", result["target"])

        result = parse_refs("Section 2, of the Act with junk")
        self.assertEqual("of", result["target"])
