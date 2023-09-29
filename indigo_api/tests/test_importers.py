import os
from io import StringIO

from cobalt import FrbrUri
from django.test import TestCase
from docpipe.pipeline import Pipeline, PipelineContext
from lxml import etree

from indigo.pipelines.base import ParseBluebellText, WrapAnnotations
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

    def test_tz_cap6(self):
        self.run_file_test("tz-cap6")

    def test_tz_with_schedule(self):
        self.run_file_test("tz-cap1")

    def test_identify_part_headings(self):
        self.run_file_test('identify-part-headings')

    def test_identify_paragraphs(self):
        self.run_file_test('identify-paragraphs')

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

  SUBPARAGRAPH 1.1.1.

    Nested paragraph.

    Text text text.

  SUBPARAGRAPH 1.1.2

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

    def test_sections_versus_paragraphs(self):
        self.assertMultiLineEqual(
            """
BODY 

SECTION 16. - CONSOLIDATION OF A DEBTOR’S ACCOUNTS

  PARAGRAPH 1.

    The Municipal Manager may -

    SUBPARAGRAPH a)

      Consolidate any separate accounts of a debtor;

    SUBPARAGRAPH b)

      Credit a payment by a debtor against my account of that debtor; and

    SUBPARAGRAPH c)

      Implement any of the measures provided for in this By-law and the policy, in relation to any arrears on any of the accounts of such debtor.

  PARAGRAPH 2.

    Subsection (1) does not apply where there is a dispute between the Municipality and a debtor referred to in that subsection concerning any specific amount claimed by the Municipality from that person.
""".strip(),
            self.html_to_bluebell("""
<p>16. <b>CONSOLIDATION OF A DEBTOR’S ACCOUNTS</b></p>
<p>1. The Municipal Manager may -</p>
<p>a) Consolidate any separate accounts of a debtor;</p>
<p>b) Credit a payment by a debtor against my account of that debtor; and</p>
<p>c) Implement any of the measures provided for in this By-law and the policy, in relation to any arrears on any of the accounts of such debtor.</p>
<p>2. Subsection (1) does not apply where there is a dispute between the Municipality and a debtor referred to in that subsection concerning any specific amount claimed by the Municipality from that person.</p>
""").strip())

    def test_sections_versus_paragraphs2(self):
        self.assertMultiLineEqual(
            """
BODY 

SECTION 10. - POWER TO RESTRICT OR DISCONNECT SUPPLY OF SERVICE

  PARAGRAPH 1.

    The Municipal Manager may restrict or disconnect the supply of any service to the premises of any user whenever such user of a service -

    SUBPARAGRAPH a)

      fails to make payment on the due date;

    SUBPARAGRAPH b)

      fails to comply with an arrangement; or

    SUBPARAGRAPH c)

      fails to comply with a condition of supply imposed by the Municipality;

    SUBPARAGRAPH d)

      tenders a negotiable instrument which is dishonoured by the bank, when presented for payment.

  PARAGRAPH 2.

    The Municipal Manager may reconnect and restore full levels of supply of any of the restricted or discontinued services only -

    SUBPARAGRAPH a)

      after the arrear debt, including the costs of disconnection or reconnection, if any, have been paid in full and any other conditions has been complied with; or

    SUBPARAGRAPH b)

      after an arrangement with the debtor has been concluded.

  PARAGRAPH 3.

    The Municipal Manager may restrict, disconnect or discontinue any service in respect of any arrear debt.
""".strip(),
            self.html_to_bluebell("""
<p>10. <b>POWER TO RESTRICT OR DISCONNECT SUPPLY OF SERVICE</b></p>
<p>1. The Municipal Manager may restrict or disconnect the supply of any service to the premises of any user whenever such user of a service -</p>
<p>a) fails to make payment on the due date;</p>
<p>b) fails to comply with an arrangement; or</p>
<p>c) fails to comply with a condition of supply imposed by the Municipality;</p>
<p>d) tenders a negotiable instrument which is dishonoured by the bank, when presented for payment.</p>
<p>2. The Municipal Manager may reconnect and restore full levels of supply of any of the restricted or discontinued services only -</p>
<p>a) after the arrear debt, including the costs of disconnection or reconnection, if any, have been paid in full and any other conditions has been complied with; or</p>
<p>b) after an arrangement with the debtor has been concluded.</p>
<p>3. The Municipal Manager may restrict, disconnect or discontinue any service in respect of any arrear debt.</p>
""").strip())

    def test_sections_versus_paragraphs3(self):
        self.assertMultiLineEqual(
            """
BODY 

SECTION 14. - Expiry and renewal of fixed-term agreements

  SUBSECTION (1)

    This section does not apply to transactions between juristic persons regardless of their annual turnover or asset value.

SECTION 15. - Pre-authorisation of repair or maintenance services

  SUBSECTION (1)

    This section applies only to a transaction or consumer agreement—
""".strip(),
            self.html_to_bluebell("""
<h1 class="western" align="justify" style="margin-top: 0cm">Expiry and renewal of fixed-term agreements</h1> <p class="western" align="left" style="margin-left: 0cm; text-indent: 0cm; margin-top: 0.02cm"><br> </p>
<p class="western" align="justify" style="margin-left: 1.89cm; margin-right: 0.24cm; text-indent: 0.35cm; line-height: 95%"><b>14. </b>(1) This section does not apply to transactions between juristic persons regardless of their annual turnover or asset value.</p>
<p class="western" align="left" style="margin-left: 0cm; text-indent: 0cm; margin-top: 0.01cm"><br> </p>
<h1 class="western">Pre-authorisation of repair or maintenance services</h1> <p class="western" align="left" style="margin-left: 0cm; text-indent: 0cm; margin-top: 0cm"><br> </p>
<p class="western" align="justify" style="margin-left: 2.79cm; text-indent: -0.54cm; line-height: 0.4cm"><b>15. </b>(1) This section applies only to a transaction or consumer agreement—</p>
""").strip())

    def test_paras_in_schedules_with_headings(self):
        self.assertMultiLineEqual(
            """
BODY 

SCHEDULE FIRST SCHEDULE (Sections 5(3) and (4))
  SUBHEADING Provisions aPPlicable to commission

  Paragraphs

  PARAGRAPH 1.

    Interpretation in Schedule.

  PARAGRAPH 2. - Terms of office and conditions of service of members

    Interpretation in Schedule

  PARAGRAPH 1.

    “member” means a member of the Commission.

  PARAGRAPH 2. - Terms of office and conditions of service of members

    SUBPARAGRAPH (1)

      Subject to this Schedule, a member shall hold office for such period, not exceeding three years, as the Minister may fix on his or her appointment.

    SUBPARAGRAPH (2)

      A member shall continue in office after the expiry of his or her term until he or she has been re-appointed or his or her successor has been appointed.

      Provided that a member shall not hold office in terms of this subparagraph for longer than six months.

    SUBPARAGRAPH (3)

      Subject to subparagraph (1) a member shall hold office on such terms and conditions as the Minister may fix in relation to members generally.

    SUBPARAGRAPH (4)

      A retiring member is eligible for re-appointment as a member: Provided that no member may be re-appointed for a third term in office.

    SUBPARAGRAPH (5)

      The terms and conditions of office of a member shall not, without the member’s consent, be altered to his or her detriment during his or her tenure of office.
""".strip(),

            self.html_to_bluebell("""
<h1>FIRST SCHEDULE (Sections 5(3) and (4))</h1> <p>Provisions aPPlicable to commission</p>
<p><br> </p>
<p><i>Paragraphs</i></p>
<p>1. Interpretation in Schedule.</p>
<p>2. Terms of office and conditions of service of members.</p>
<p><br> </p>
<p><i>Interpretation</i> <i>in</i> <i>Schedule</i></p>
<p>1. “member” means a member of the Commission.</p>
<p><br> </p>
<p><i>Terms</i> <i>of</i> <i>office</i> <i>and</i> <i>conditions</i> <i>of</i> <i>service</i> <i>of</i> <i>members</i></p>
<p>2. (1) Subject to this Schedule, a member shall hold office for such period, not exceeding three years, as the Minister may fix on his or her appointment.</p>
<p>(2) A member shall continue in office after the expiry of his or her term until he or she has been re-appointed or his or her successor has been appointed.</p>
<p>Provided that a member shall not hold office in terms of this subparagraph for longer than six months.</p>
<p>(3) Subject to subparagraph (1) a member shall hold office on such terms and conditions as the Minister may fix in relation to members generally.</p>
<p>(4) A retiring member is eligible for re-appointment as a member: Provided that no member may be re-appointed for a third term in office.</p>
<p>(5) The terms and conditions of office of a member shall not, without the member’s consent, be altered to his or her detriment during his or her tenure of office.</p>
""").strip())

    def test_paras_in_schedules_without_headings(self):
        self.assertMultiLineEqual(
            """
BODY 

SCHEDULE SECOND SCHEDULE (Section 5(5))
  SUBHEADING Ancillary Powers of Commission

  PARAGRAPH 1.

    To acquire premises.

  PARAGRAPH 2.

    To buy, take in exchange, hire or otherwise acquire movable property.

  PARAGRAPH 3.

    To maintain, alter or improve property acquired by it.

  PARAGRAPH 4.

    To mortgage any assets, or part of any assets.

  PARAGRAPH 5.

    To open bank accounts in the name of the Commission.

  PARAGRAPH 6.

    To insure against losses, damages, risks and liabilities which it may incur.

  PARAGRAPH 7.

    In consultation with the Minister, to establish and administer such funds.
""".strip(),

            self.html_to_bluebell("""
<h1>SECOND SCHEDULE (Section 5(5))</h1>
<p>Ancillary Powers of Commission</p>
<p>1. To acquire premises.</p>
<p>2. To buy, take in exchange, hire or otherwise acquire movable property.</p>
<p>3. To maintain, alter or improve property acquired by it.</p>
<p>4. To mortgage any assets, or part of any assets.</p>
<p>5. To open bank accounts in the name of the Commission.</p>
<p>6. To insure against losses, damages, risks and liabilities which it may incur.</p>
<p>7. In consultation with the Minister, to establish and administer such funds.</p>
""").strip())

    def test_schedules(self):
        self.assertMultiLineEqual(
            """
BODY 

SCHEDULE FIRST SCHEDULE (Sections 5(3) and (4))
  SUBHEADING Provisions applicable to Commission

  Body

SCHEDULE Schedule 1
  SUBHEADING Heading

  Body

SCHEDULE Schedule 2

  Body, no subheading

SCHEDULE Schedule

  PART I - Heading

    Body

SCHEDULE Schedule
  SUBHEADING Heading

  PART I - Heading

    Body

SCHEDULE Schedule 3

  Body, no subheading
""".strip(),

            self.html_to_bluebell("""
<p>FIRST SCHEDULE (Sections 5(3) and (4))</p>
<p>Provisions <i>applicable</i> to Commission</p>
<p>Body</p>

<p>Schedule 1</p>
<p>Heading</p>
<p>Body</p>

<p>Schedule 2</p>
<p>Body, no subheading</p>

<p>Schedule</p>
<p>Part I: Heading</p>
<p>Body</p>

<p>Schedule</p>
<p>Heading</p>
<p>Part I: Heading</p>
<p>Body</p>

<p>Schedule 3</p>
<p>Body, no subheading</p>
""").strip())

    def test_annexes(self):
        self.assertMultiLineEqual(
            """
BODY 

SECTION 1. - Heading

  Section body

ANNEXURE FIRST ANNEX (Sections 5(3) and (4))
  SUBHEADING Heading

  PARAGRAPH 1. - Heading in annex

    Paragraph body in annex

ANNEXURE Annexure 1 Heading

  Body

ANNEXURE Annex

  Body
""".strip(),

            self.html_to_bluebell("""
<p>1. Heading</p>
<p>Section body</p>

<p>FIRST ANNEX (Sections 5(3) and (4))</p>
<p>Heading</p>

<p>1. Heading in annex</p>
<p>Paragraph body in annex</p>

<p>Annexure 1 Heading</p>
<p>Body</p>

<p>Annex</p>
<p>Body</p>
""").strip())

    def test_appendixes(self):
        self.assertMultiLineEqual(
            """
BODY 

SECTION 1. - Heading

  Section body

APPENDIX FIRST APPENDIX (Sections 5(3) and (4))
  SUBHEADING Heading

  PARAGRAPH 1. - Heading in appendix

    Paragraph body in appendix

APPENDIX Appendix 1 Heading

  Body

APPENDIX Appendix

  Body
""".strip(),

            self.html_to_bluebell("""
<p>1. Heading</p>
<p>Section body</p>

<p>FIRST APPENDIX (Sections 5(3) and (4))</p>
<p>Heading</p>

<p>1. Heading in appendix</p>
<p>Paragraph body in appendix</p>

<p>Appendix 1 Heading</p>
<p>Body</p>

<p>Appendix</p>
<p>Body</p>
""").strip())

    def test_attachments(self):
        self.assertMultiLineEqual(
            """
BODY 

SECTION 1. - Heading

  Section body

ATTACHMENT FIRST ATTACHMENT (Sections 5(3) and (4))
  SUBHEADING Heading

  PARAGRAPH 1. - Heading in attachment

    Paragraph body in attachment

ATTACHMENT Attachment 1 Heading

  Body

ATTACHMENT Attachment

  Body
""".strip(),

            self.html_to_bluebell("""
<p>1. Heading</p>
<p>Section body</p>

<p>FIRST ATTACHMENT (Sections 5(3) and (4))</p>
<p>Heading</p>

<p>1. Heading in attachment</p>
<p>Paragraph body in attachment</p>

<p>Attachment 1 Heading</p>
<p>Body</p>

<p>Attachment</p>
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

    def test_numbered_paragraphs_with_subparagraphs(self):
        self.assertMultiLineEqual(
            """
BODY 

SCHEDULE Schedule

  PARAGRAPH 1. - foo

    SUBPARAGRAPH (a)

      item

    SUBPARAGRAPH (b)

      item

    SUBPARAGRAPH (c)

      item

      SUBPARAGRAPH (i)

        item

      SUBPARAGRAPH (ii)

        item
""".strip(),

            self.html_to_bluebell("""
<p>Schedule</p>
<p>1. foo</p>
<p>(a) item</p>
<p>(b) item</p>
<p>(c) item</p>
<p>(i) item</p>
<p>(ii) item</p>
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

    def test_wrap_intro_wrapup_annotations(self):
        # note: we have to ParseBluebellText, then WrapAnnotations,
        # because simply using etree.fromstring(xml) doesn't reproduce what happens on import
        context = PipelineContext(pipeline=Pipeline([ParseBluebellText(), WrapAnnotations()]))
        context.frbr_uri = FrbrUri.parse('/akn/za/act/2020/1')
        context.fragment = None
        context.fragment_id_prefix = None

        context.text = open(os.path.join(os.path.dirname(__file__), f'importer_fixtures/wrap-annotations.txt')).read()
        context.pipeline(context)
        # remove meta block(s)
        for meta in context.xml.xpath('//a:meta', namespaces={'a': WrapAnnotations.ns}):
            meta.getparent().remove(meta)

        actual = etree.tostring(context.xml, encoding='unicode', pretty_print=True)
        expected = open(os.path.join(os.path.dirname(__file__), f'importer_fixtures/wrap-annotations.xml')).read()
        self.assertMultiLineEqual(expected, actual)


class ImporterDocxTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'taxonomy_topics', 'work', 'drafts']

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
            '‘‘this thing’’ means “that” and ‟this\'\''),
            '“this thing” means “that” and “this"')

    def test_normalise_single_quotes(self):
        self.assertEqual(self.pipeline_text(
            "‘this thing’ means ‛that’ and ‟this''"),
            """‘this thing’ means ‘that’ and “this\"""")

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
