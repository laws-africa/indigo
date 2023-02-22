from io import StringIO

from django.test import TestCase


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


class ImporterDocxTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'work', 'drafts']

    def setUp(self):
        self.importer = Importer()
        self.pipeline = self.importer.get_docx_pipeline()

        self.work = Work.objects.get(pk=1)
        self.doc = Document(work=self.work, language=Language.objects.first())

        # remove the docx to html conversion, and the slaw parsing,
        # but keep the cleanup and the html-to-slaw parts
        self.pipeline.stages = self.pipeline.stages[1:-2]
        self.context = ImportContext(self.pipeline)
        self.context.doc = self.doc

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

"""some non-breaking spaces

some tabs and newlines""")

    def test_remove_and_merge_inlines(self):
        self.assertMultiLineEqual(self.pipeline_html("""
<p>some <sup></sup> empty tags <sup></sup></p>
""").strip(),

"""some empty tags""")

    def test_merge_ul(self):
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

"""text

* item 1
* item 2


finish""")

    def test_cleanup_tables(self):
        self.assertMultiLineEqual(self.pipeline_html("""
<table class="bordered" style="font-size: 20px">
  <thead>
    <tr>
      <th class="header" colspan="2" width="80%">
        <span style="font-weight: bold">header</span> one
      </th>
      <th style="height: 2em; border-bottom: 1px solid red">header two</th>
      <th>header three</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="90%">cell one</td>
      <td>cell two</td>
      <td>cell three</td>
    </tr>
  </tbody>
</table>
""").strip(),

"""{| 
|-
! colspan="2" | header one
! header two
! header three
|-
| cell one
| cell two
| cell three
|-
|}""")


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
