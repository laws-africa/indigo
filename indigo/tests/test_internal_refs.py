from django.test import TestCase
from cobalt import AkomaNtosoDocument

from indigo.analysis.refs.sections import InternalRefsResolver, ProvisionRef
from indigo_api.tests.fixtures import document_fixture


class InternalRefsResolverTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.resolver = InternalRefsResolver()
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
        refs = self.resolver.resolve_references("Section 1", self.doc)
        self.assertEqual([ProvisionRef("1", 8, 9, "sec_1")], refs[0])

    def test_initial_no_match(self):
        self.assertEqual(self.resolver.resolve_references("Section 3(a)", self.doc), [])

    def test_ambiguous(self):
        refs = self.resolver.resolve_references("(a)", self.doc)
        self.assertEqual([ProvisionRef("(a)", 0, 3, "sec_1__subsec_a")], refs[0])

        refs = self.resolver.resolve_references("(a)(2)", self.doc)
        self.assertEqual([
            ProvisionRef("(a)", 0, 3, "sec_1__subsec_a"),
            ProvisionRef("(2)", 3, 6, "sec_1__subsec_a__para_2")
        ], refs[0])

    def test_nested(self):
        refs = self.resolver.resolve_references("section 1(a)", self.doc)
        self.assertEqual([
            ProvisionRef("1", 8, 9, "sec_1"),
            ProvisionRef("(a)", 9, 12, "sec_1__subsec_a")
        ], refs[0])

        refs = self.resolver.resolve_references("section 2(a)(2)", self.doc)
        self.assertEqual([
            ProvisionRef("2", 8, 9, "sec_2"),
            ProvisionRef("(a)", 9, 12, "sec_2__subsec_a"),
            ProvisionRef("(2)", 12, 15, "sec_2__subsec_a__para_2")
        ], refs[0])

    def test_nested_truncated(self):
        refs = self.resolver.resolve_references("section 2(a)(8)", self.doc)
        self.assertEqual([
            ProvisionRef("2", 8, 9, "sec_2"),
            ProvisionRef("(a)", 9, 12, "sec_2__subsec_a"),
        ], refs[0])

