import os
from io import StringIO

from cobalt import FrbrUri
from django.test import TestCase
from docpipe.pipeline import PipelineContext
from lxml import etree

from indigo.pipelines.base import WrapAnnotations
from indigo_api.importers.base import parse_page_nums, Importer, ImportContext
from indigo_api.models import Document, Work, Language


class ImporterTestCase(TestCase):
    def setUp(self):
        self.importer = Importer()

    def test_parse_page_nums_good(self):
        self.assertEqual(parse_page_nums("1"), [1])
        self.assertEqual(parse_page_nums("1-3"), [(1, 3)])
        self.assertEqual(parse_page_nums("1 -3 "), [(1, 3)])
        self.assertEqual(parse_page_nums(" 1, 1 -3, 99  "), [1, (1, 3), 99])

    def test_parse_page_nums_bad(self):
        with self.assertRaises(ValueError):
            parse_page_nums(" -1,  ")
        with self.assertRaises(ValueError):
            parse_page_nums(" a  ")
        with self.assertRaises(ValueError):
            parse_page_nums(" 1-  ")

        self.assertEqual(parse_page_nums(" , ,  "), [])


class ImporterBluebellTestCase(TestCase):
    maxDiff = None
    # show diffs, no matter how big
    _diffThreshold = 999999999

    def setUp(self):
        self.importer = Importer()
        self.maxDiff = None
        self.pipeline = self.importer.html_to_bluebell()
        self.context = ImportContext(self.pipeline)
        self.context.frbr_uri = FrbrUri.parse('/akn/za/act/2020/1')

    def html_to_bluebell(self, html):
        """ Run the provided html text through the pipeline and return the resulting context.text
        """
        self.context.html_text = html
        self.pipeline(self.context)
        return self.context.text

    def run_file_test(self, prefix, update=False):
        html = open(os.path.join(os.path.dirname(__file__), f'importer_fixtures/{prefix}.html')).read()

        self.context.html_text = html
        self.context.pipeline(self.context)

        actual = self.context.text + '\n'
        if update:
            # update the fixture to match the actual
            open(os.path.join(os.path.dirname(__file__), f'importer_fixtures/{prefix}.txt'), 'w').write(actual)
        expected = open(os.path.join(os.path.dirname(__file__), f'importer_fixtures/{prefix}.txt')).read()
        self.assertMultiLineEqual(expected, actual)

    def test_zw_cpa(self):
        self.run_file_test("zw-cpa")

    def test_za_cpa(self):
        self.run_file_test("za-cpa")

    def test_mu_convention(self):
        self.run_file_test("mu-convention")

    def test_identify_part_headings(self):
        self.run_file_test('identify-part-headings')

    def test_tables(self):
        self.run_file_test("tables")

    def test_debate(self):
        self.context.frbr_uri = FrbrUri.parse('/akn/za/debate/2020/1')
        self.run_file_test("debate")

    def test_hierarchicalize(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH 1.

    First paragraph of text that is long enough not to be a heading lorum ipsum lorum ipsu lorum ipsu lorum ipsu lorum ipsu lorum ipsu lorum ipsummmmmm

  PARAGRAPH 1.1.1.

    Nested paragraph.

    Text text text.

  PARAGRAPH 1.1.2

    Also this one.

    1.1.3Not this one.

  PARAGRAPH 123

    Section
""".strip(),
            self.html_to_bluebell("""
<p>1. First paragraph of text that is long enough not to be a heading lorum ipsum lorum ipsu lorum ipsu lorum ipsu lorum ipsu lorum ipsu lorum ipsummmmmm</p>

<p>1.1.1. Nested paragraph.</p>

<p>Text text text.</p>

<p>1.1.2 Also this one.</p>

<p>1.1.3Not this one.</p>

<p>123 Section</p>""").strip())

    def test_identify_sections(self):
        self.assertMultiLineEqual(
            """BODY 

  SECTION 1. - Section heading

    Section body

  SECTION 2. - Section heading that is extra long and verbose but is bold and therefore can safely be taken as a section heading

    Section 2 body that is substantial and shouldn't be mistaken for a section heading, so that the next line is a paragraph.

    PARAGRAPH 3.

      Numbered paragraph with a very long body that looks like a section heading but is not and should not be mistaken for a section heading.""",
            self.html_to_bluebell("""
<p>1. Section heading</p>
<p>Section body</p>

<p><b>2.</b> <b>Section heading that is extra long and verbose but is bold and therefore can safely be taken as a section heading</p>
<p>Section 2 body that is substantial and shouldn't be mistaken for a section heading, so that the next line is a paragraph.</p>

<p>3. Numbered paragraph with a very long body that looks like a section heading but is not and should not be mistaken for a section heading.</p>
    """).strip())

    def test_escape(self):
        self.assertMultiLineEqual(
            """BODY 

  SECTION 1. - Section heading

    \SECTION should be escaped

    these should be escaped:

    \{\{

    \PREAMBLE

    \{\{""",
            self.html_to_bluebell("""
<p>1. Section heading</p>
<p>SECTION should be escaped</p>

<p>these should be escaped:</p>
<p>{{</p>
<p>PREAMBLE</p>
<ul>
  <li>{{</li>
</ul>
""").strip())

    def test_preface_preamble(self):
        self.assertMultiLineEqual(
            """PREFACE 

  Preface

  Some text

PREAMBLE 

  Preamble

  Some text

BODY 

  SECTION 1. - Section heading

    Section body

    These should be ignored

    Preface

    Preamble""",
            self.html_to_bluebell("""
<p>Preface</p>
<p>Some text</p>
<p>Preamble</p>
<p>Some text</p>
<p>1. Section heading</p>
<p>Section body</p>

<p>These should be ignored</p>
<p>Preface</p>
<p>Preamble</p>
""").strip())

    def test_section_headings(self):
        self.assertMultiLineEqual(
            """
BODY 

  SECTION 2.

    SUBSECTION (1)

      directly into subsection no heading

  SECTION 3. - A short heading

    SUBSECTION (1)

      directly into subsection but with a heading

  SECTION 4. - A very long heading that is too long to normally look like a heading but is bold, and therefore assumed to be a section heading

    SUBSECTION (1)

      directly into subsection but with a heading

      PARAGRAPH 5.

        looks like a section initially but should be a paragraph

      PARAGRAPH 6.

        because the next element is not its content, but another akn-block!
""".strip(),
            self.html_to_bluebell("""
<p>2. (1) directly into subsection no heading</p>

<p>A short heading</p>
<p>3. (1) directly into subsection but with a heading</p>

<p><b>A very long heading that is too long to normally look like a heading but is bold, and therefore assumed to be a section heading</b></p>
<p>4. (1) directly into subsection but with a heading</p>
<p>5. looks like a section initially but should be a paragraph</p>
<p>6. because the next element is not its content, but another akn-block!</p>
""").strip())

    def test_schedules(self):
        self.assertMultiLineEqual(
            """
BODY 

SCHEDULE FIRST SCHEDULE
  SUBHEADING (Sections 5(3) and (4))

  Body

SCHEDULE Schedule 1 Heading

  Body

SCHEDULE Schedule

  Body
""".strip(),

            self.html_to_bluebell("""
<p>FIRST SCHEDULE (Sections 5(3) and (4))</p>
<p>Body</p>

<p>Schedule 1 Heading</p>
<p>Body</p>

<p>Schedule</p>
<p>Body</p>
""").strip())

    def test_annexes(self):
        self.assertMultiLineEqual(
            """
BODY 

  SECTION 1. - Heading

    Section body

ANNEX  - FIRST ANNEX
  SUBHEADING (Sections 5(3) and (4))

  Body

  SECTION 1. - Heading in annex

    Section body in annex

ANNEX  - 1 Heading

  Body

ANNEX 

  Body
""".strip(),

            self.html_to_bluebell("""
<p>1. Heading</p>
<p>Section body</p>

<p>FIRST ANNEX (Sections 5(3) and (4))</p>
<p>Body</p>

<p>1. Heading in annex</p>
<p>Section body in annex</p>

<p>Annexure 1 Heading</p>
<p>Body</p>

<p>Annex</p>
<p>Body</p>
""").strip())

    def test_subparagraphs_1(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (a)

    foo

    SUBPARAGRAPH (i)

      item

    SUBPARAGRAPH (ii)

      item

    SUBPARAGRAPH (iii)

      item

      SUBPARAGRAPH (aa)

        item

      SUBPARAGRAPH (bb)

        item
""".strip(),

            self.html_to_bluebell("""
<p>(a) foo</p>
<p>(i) item</p>
<p>(ii) item</p>
<p>(iii) item</p>
<p>(aa) item</p>
<p>(bb) item</p>
""").strip())

    def test_paragraphs_with_inline_whitespace_at_start(self):
        """ All but underlined whitespace will be handled."""
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (a)

    chief electoral officer;

  PARAGRAPH (b)

    deputy chief electoral officer; and

  PARAGRAPH (c)

    electoral officer.

  PARAGRAPH (d)

    whitespace before d too

  PARAGRAPH (e)

    bold whitespace before e

  PARAGRAPH (f)

    bold whitespace before f
""".strip(),

            self.html_to_bluebell("""
<p>	(<em>a</em>)	chief electoral officer;</p>
<p>	(<em>b</em>)	deputy chief electoral officer; and</p>
<p><em>	</em>(<em>c</em>)	electoral officer.</p>
<p>  <em>	(d)</em>	whitespace before d too</p>
<p><b>	(e)</b>	bold whitespace before e</p>
<p><b> </b>(f) bold whitespace before f</p>
""").strip())

    def test_subparagraphs_2(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (a)

    foo

    SUBPARAGRAPH (i)

      item

    SUBPARAGRAPH (ii)

      item

  PARAGRAPH (c)

    item
""".strip(),

            self.html_to_bluebell("""
<p>(a) foo</p>
<p>(i) item</p>
<p>(ii) item</p>
<p>(c) item</p>
""").strip())

    def test_subparagraphs_hij(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (h)

    item

  PARAGRAPH (i)

    item

  PARAGRAPH (j)

    item
""".strip(),

            self.html_to_bluebell("""
<p>(h) item</p>
<p>(i) item</p>
<p>(j) item</p>
""").strip())

    def test_subparagraphs_hi(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (h)

    item

  PARAGRAPH (i)

    item

""".strip(),

            self.html_to_bluebell("""
<p>(h) item</p>
<p>(i) item</p>
""").strip())

    def test_subparagraphs_hij_i_ii_iii(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (h)

    item

  PARAGRAPH (i)

    item

  PARAGRAPH (j)

    item

    SUBPARAGRAPH (i)

      item

    SUBPARAGRAPH (ii)

      item

    SUBPARAGRAPH (iii)

      item
""".strip(),

            self.html_to_bluebell("""
<p>(h) item</p>
<p>(i) item</p>
<p>(j) item</p>
<p>(i) item</p>
<p>(ii) item</p>
<p>(iii) item</p>
""").strip())

    def test_subparagraphs_hij_I_II_j(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (h)

    item

  PARAGRAPH (i)

    item

    SUBPARAGRAPH (I)

      item

    SUBPARAGRAPH (II)

      item

  PARAGRAPH (j)

    item

    SUBPARAGRAPH (i)

      item

    SUBPARAGRAPH (ii)

      item
""".strip(),

            self.html_to_bluebell("""
<p>(h) item</p>
<p>(i) item</p>
<p>(I) item</p>
<p>(II) item</p>
<p>(j) item</p>
<p>(i) item</p>
<p>(ii) item</p>
""").strip())

    def test_subparagraphs_uvx(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (u)

    item

  PARAGRAPH (v)

    item

  PARAGRAPH (w)

    item

  PARAGRAPH (x)

    item
""".strip(),

            self.html_to_bluebell("""
<p>(u) item</p>
<p>(v) item</p>
<p>(w) item</p>
<p>(x) item</p>
""").strip())

    def test_subparagraphs_yz_aa_bb(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (y)

    item

  PARAGRAPH (z)

    item

  PARAGRAPH (aa)

    item

  PARAGRAPH (bb)

    item
""".strip(),

            self.html_to_bluebell("""
<p>(y) item</p>
<p>(z) item</p>
<p>(aa) item</p>
<p>(bb) item</p>
""").strip())

    def test_subparagraphs_z_AA_BB(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (z)

    item

    SUBPARAGRAPH (AA)

      item

    SUBPARAGRAPH (BB)

      item
""".strip(),

            self.html_to_bluebell("""
<p>(z) item</p>
<p>(AA) item</p>
<p>(BB) item</p>
""").strip())

    def test_subparagraphs_deeply_nested(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (a)

    item

  PARAGRAPH (b)

    item

    SUBPARAGRAPH (i)

      item

      SUBPARAGRAPH (aa)

        item

      SUBPARAGRAPH (bb)

        item

    SUBPARAGRAPH (ii)

      item

  PARAGRAPH (c)

    item

    SUBPARAGRAPH (i)

      item

    SUBPARAGRAPH (ii)

      item

    SUBPARAGRAPH (iii)

      item
""".strip(),

            self.html_to_bluebell("""
<p>(a) item</p>
<p>(b) item</p>
<p>(i) item</p>
<p>(aa) item</p>
<p>(bb) item</p>
<p>(ii) item</p>
<p>(c) item</p>
<p>(i) item</p>
<p>(ii) item</p>
<p>(iii) item</p>
""").strip())

    def test_subparagraphs_h_i_ii_i(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH (h)

    item

    SUBPARAGRAPH (i)

      item

    SUBPARAGRAPH (ii)

      item

  PARAGRAPH (i)

    item
""".strip(),

            self.html_to_bluebell("""
<p>(h) item</p>
<p>(i) item</p>
<p>(ii) item</p>
<p>(i) item</p>
""").strip())

    def test_subparagraphs_dotted_nums(self):
        self.assertMultiLineEqual(
            """
BODY 

  PARAGRAPH 9.2.1

    item

    SUBPARAGRAPH 9.2.1.1

      item

    SUBPARAGRAPH 9.2.1.2

      item

  PARAGRAPH 9.2.2

    item
""".strip(),

            self.html_to_bluebell("""
<p>9.2.1 item</p>
<p>9.2.1.1 item</p>
<p>9.2.1.2 item</p>
<p>9.2.2 item</p>
""").strip())

    def test_wrap_annotations(self):
        context = PipelineContext(pipeline=None)
        xml = '''
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <content>
    <p>hi</p>
    <p>[Regular annotation.]</p>
    <p>[Annotation with a 2<sup>nd</sup> in it<i>]</i></p>
    <p><b>[</b>Annotation that starts with a bold open]</p>
    <p>[inline annotation (or is it?)] with text following</p>
    <p>[text in squares] [and some more]</p>
  </content>
</akomaNtoso>
'''
        context.xml = etree.fromstring(xml)
        WrapAnnotations()(context)
        new_xml_text = etree.tostring(context.xml, encoding='unicode')
        self.assertMultiLineEqual('''<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <content>
    <p>hi</p>
    <p><remark status="editorial">[Regular annotation.]</remark></p>
    <p><remark status="editorial">[Annotation with a 2<sup>nd</sup> in it<i>]</i></remark></p>
    <p><remark status="editorial"><b>[</b>Annotation that starts with a bold open]</remark></p>
    <p>[inline annotation (or is it?)] with text following</p>
    <p>[text in squares] [and some more]</p>
  </content>
</akomaNtoso>''', new_xml_text)


class ImporterDocxTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'work', 'drafts']

    def setUp(self):
        self.importer = Importer()
        self.pipeline = self.importer.get_docx_pipeline()

        self.work = Work.objects.get(pk=1)
        self.doc = Document(work=self.work, language=Language.objects.first())

        # remove the docx to html conversion, and the bluebell parsing,
        # but keep the html-to-bluebell stages
        self.pipeline.stages = self.pipeline.stages[1].stages
        self.context = ImportContext(self.pipeline)
        self.context.doc = self.doc
        self.context.frbr_uri = self.work.work_uri

    def pipeline_html(self, html):
        """ Run the provided html text through the pipeline and return the resulting context.text
        """
        self.context.html_text = html
        self.pipeline(self.context)
        return self.context.text

    def test_import_bad_docx(self):
        importer = Importer()
        doc = Document.objects.first()
        f = StringIO()
        with self.assertRaises(ValueError):
            importer.import_from_docx(f, doc)

    def test_normalise_whitespace(self):
        self.assertMultiLineEqual(self.pipeline_html("""
<p>some&nbsp;non-breaking\xA0spaces</p>
<p>   some\t tabs

and
  
newlines</p>
""").strip(),

"""PREFACE 

  some non-breaking spaces

some tabs and newlines""")

    def test_remove_and_merge_inlines(self):
        self.assertMultiLineEqual(self.pipeline_html("""
<p>some <sup></sup> empty tags <sup></sup></p>
""").strip(),

"""PREFACE 

  some  empty tags""")

    def test_merge_ul(self):
        # TODO: nuke this test?
        self.assertMultiLineEqual(self.pipeline_html("""
<p>text</p>
<ul>
<li>item 1</li>
</ul>
<ul>
<li>item 2</li>
</ul>
<p>finish</p>
""").strip(),

"""PREFACE 

  text

  item 1

  item 2

  finish""")

    def test_cleanup_tables(self):
        # TODO: tweak pipeline stages and output for this test? (real-life table imports work)
        self.assertMultiLineEqual(self.pipeline_html("""
<table class="bordered" style="font-size: 20px">
  <thead>
    <tr>
      <th class="header" colspan="2" width="80%">
        <p><span style="font-weight: bold">header</span> one</p>
      </th>
      <th style="height: 2em; border-bottom: 1px solid red"><p>header two</p></th>
      <th><p>header three</p></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="90%"><p>cell one</p></td>
      <td><p>cell two</p></td>
      <td><p>cell three</p></td>
    </tr>
  </tbody>
</table>
""").strip(),

"""PREFACE 

  TABLE.bordered{style font-size: 20px}
    TR
      TH.header{colspan 2|style width: 100%}
        header one

      TH{style height: 2em}
        header two

      TH
        header three

    TR
      TC{style width: 100%}
        cell one

      TC
        cell two

      TC
        cell three""")


class ImporterPDFTestCase(TestCase):
    def setUp(self):
        self.importer = Importer()
        self.pipeline = self.importer.get_pdf_pipeline()
        # keep just the cleanup part of the pipeline
        # skip the first three (PDF-related), and the last five (parsing)
        self.pipeline.stages = self.pipeline.stages[3:-5]
        self.context = ImportContext(self.pipeline)

    def pipeline_text(self, text):
        """ Run the provided text through the pipeline and return the resulting context.text
        """
        self.context.text = text
        self.pipeline(self.context)
        return self.context.text

    def test_remove_boilerplate(self):
        text = """text
    this gazette is also available in paper

page 2 of 22
-------------
PUBLISHED IN THE PROVINCIAL GAZETTE

22 Augest 2018

more text
"""
        self.assertEqual(self.pipeline_text(text), "text\n\n\n\n\n\nmore text\n")

    def test_dont_remove_blanks(self):
        text = """We're in a form:

Person________(id number)

Person _________ (id number)

Person _________(id number)

Person_________ (id number)

more text
"""
        self.assertEqual(self.pipeline_text(text), "We're in a form:\n\nPerson________(id number)\n\nPerson _________ (id number)\n\nPerson _________(id number)\n\nPerson_________ (id number)\n\nmore text\n")

    def test_break_nested_lists(self):
        self.assertEqual(self.pipeline_text(
            'stored, if known; (b) the number of trolleys'),
            "stored, if known;\n(b) the number of trolleys")

        self.assertEqual(self.pipeline_text(
            "(5) The officer-in-Charge may – (a) remove all withered natural flowers, faded or damaged artificial flowers and any receptacle placed on a grave; or\n(b) 30 days after publishing a general"),
            "(5) The officer-in-Charge may –\n(a) remove all withered natural flowers, faded or damaged artificial flowers and any receptacle placed on a grave; or\n(b) 30 days after publishing a general")

        self.assertEqual(self.pipeline_text(
            "(2) No person may – (a) plant, cut or remove plants, shrubs or flowers on a grave without the permission of the officer-in-charge; (b) plant, cut or remove plants, shrubs or flowers on the berm section; or"),
            "(2) No person may –\n(a) plant, cut or remove plants, shrubs or flowers on a grave without the permission of the officer-in-charge;\n(b) plant, cut or remove plants, shrubs or flowers on the berm section; or")

        self.assertEqual(self.pipeline_text(
            '(b) its successor in title; or (c) a structure or person exercising a delegated power or carrying out an instruction, where any power in these By-laws, has been delegated or sub-delegated or an instruction given as contemplated in, section 59 of the Local Government: Municipal Systems Act, 2000 (Act No. 32 of 2000); or (d) a service provider fulfilling a responsibility under these By-laws, assigned to it in terms of section 81(2) of the Local Government: Municipal Systems Act, 2000, or any other law, as the case may be;'),
            "(b) its successor in title; or\n(c) a structure or person exercising a delegated power or carrying out an instruction, where any power in these By-laws, has been delegated or sub-delegated or an instruction given as contemplated in, section 59 of the Local Government: Municipal Systems Act, 2000 (Act No. 32 of 2000); or\n(d) a service provider fulfilling a responsibility under these By-laws, assigned to it in terms of section 81(2) of the Local Government: Municipal Systems Act, 2000, or any other law, as the case may be;")

    def test_break_at_likely_subsections(self):
        self.assertEqual(self.pipeline_text(
            '(c) place a metal cot on any grave. (3) A person may only erect, place or leave, an object or decoration on a grave during the first 30 days following the burial. (4) Natural or artificial flowers contained in receptacles may be placed on a grave at any time, but in a grave within a berm section or with a headstone, such flowers may only be placed in the socket provided. (5) The officer-in-Charge may – (a) remove all withered natural flowers, faded or damaged artificial flowers and any receptacle placed on a grave; or'),
            "(c) place a metal cot on any grave.\n(3) A person may only erect, place or leave, an object or decoration on a grave during the first 30 days following the burial.\n(4) Natural or artificial flowers contained in receptacles may be placed on a grave at any time, but in a grave within a berm section or with a headstone, such flowers may only be placed in the socket provided.\n(5) The officer-in-Charge may – (a) remove all withered natural flowers, faded or damaged artificial flowers and any receptacle placed on a grave; or")

    def test_break_lines_at_likely_section_titles(self):
        self.assertEqual(self.pipeline_text(
            'foo bar. New section title 62. (1) For the purpose'),
            "foo bar.\nNew section title\n62. (1) For the purpose")
        self.assertEqual(self.pipeline_text(
            'foo bar. New section title 62.(1) For the purpose'),
            "foo bar.\nNew section title\n62.(1) For the purpose")
        self.assertEqual(self.pipeline_text(
            'New section title 62. (1) For the purpose'),
            "New section title\n62. (1) For the purpose")
        self.assertEqual(self.pipeline_text(
            'New section title 62.(1) For the purpose'),
            "New section title\n62.(1) For the purpose")

    def test_clean_up_wrapped_definition_lines_after_pdf(self):
        self.assertEqual(self.pipeline_text(
            '"agricultural holding" means a portion of land not less than 0.8 hectares in extent used solely or mainly for the purpose of agriculture, horticulture or for breeding or keeping domesticated animals, poultry or bees; "approved" means as approved by the Council; "bund wall" means a containment wall surrounding an above ground storage tank, constructed of an impervious material and designed to contain 110% of the contents of the tank; "certificate of fitness" means a certificate contemplated in section 20; "certificate of registration" means a certificate contemplated in section 35;'),
            '"agricultural holding" means a portion of land not less than 0.8 hectares in extent used solely or mainly for the purpose of agriculture, horticulture or for breeding or keeping domesticated animals, poultry or bees;\n"approved" means as approved by the Council;\n"bund wall" means a containment wall surrounding an above ground storage tank, constructed of an impervious material and designed to contain 110% of the contents of the tank;\n"certificate of fitness" means a certificate contemplated in section 20;\n"certificate of registration" means a certificate contemplated in section 35;')

    def test_break_at_CAPCASE_TO_Normal_Case(self):
        self.assertEqual(self.pipeline_text(
            'CHAPTER 3 PARKING METER PARKING GROUNDS Place of parking 7. No person may park or cause or permit to be parked any vehicle or allow a vehicle to be or remain in a parking meter parking ground otherwise than in a parking bay.'),
            "CHAPTER 3 PARKING METER PARKING GROUNDS\nPlace of parking 7. No person may park or cause or permit to be parked any vehicle or allow a vehicle to be or remain in a parking meter parking ground otherwise than in a parking bay.")

    def test_should_unbreak_simple_lines(self):
        self.assertEqual(self.pipeline_text("""
8.2.3 an additional fee or tariff, which is
to be determined by the City in its
sole discretion, in respect of additional
costs incurred or services.
8.3 In the event that a person qualifies for
a permit, but has motivated in writing
the inability to pay the fee contemplated."""), """
8.2.3 an additional fee or tariff, which is to be determined by the City in its sole discretion, in respect of additional costs incurred or services.
8.3 In the event that a person qualifies for a permit, but has motivated in writing the inability to pay the fee contemplated.""")

    def test_should_not_unbreak_section_headers(self):
        self.assertEqual(self.pipeline_text("""
8.4.3 must be a South African citizen, failing which, must be in possession of
a valid work permit which includes, but is not limited to, a refugee
permit; and
8.4.4 must not employ and actively utilise the services of more than 20
(twenty) persons."""), """
8.4.3 must be a South African citizen, failing which, must be in possession of a valid work permit which includes, but is not limited to, a refugee permit; and
8.4.4 must not employ and actively utilise the services of more than 20
(twenty) persons.""")

    def test_fix_quotes(self):
        self.assertEqual(self.pipeline_text(
            '’’this thing’’ means “that” and ‟this\'\''),
            '"this thing" means "that" and "this"')

    def test_whitespace_subsections(self):
        self.assertEqual(self.pipeline_text("""
(a) not changed
( b ) changed
(b  ) changed
(bb ) changed
        """), """
(a) not changed
(b) changed
(b) changed
(bb) changed
        """)

    def test_whitespace_subsections2(self):
        self.assertEqual(self.pipeline_text(
            "report on the im- plementation"),
            "report on the implementation")
