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
