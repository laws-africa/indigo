import os
import tempfile
import datetime

from django.test import testcases, override_settings

from indigo_api.importers.pdfs import pdf_count_pages
from indigo_api.models import Work


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class DocumentViewsTest(testcases.TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work', 'editor', 'drafts', 'published']

    def setUp(self):
        self.assertTrue(self.client.login(username='email@example.com', password='password'))

    def test_published_document(self):
        response = self.client.get('/documents/1/')
        self.assertEqual(response.status_code, 200)

    def test_draft_document(self):
        response = self.client.get('/documents/10/')
        self.assertEqual(response.status_code, 200)

    def test_create_from_docx(self):
        work = Work.objects.get_for_frbr_uri('/akn/za/act/2014/10')

        fname = os.path.join(os.path.dirname(__file__), '../fixtures/act-2-1998.docx')
        f = open(fname, 'rb')

        response = self.client.post('/works/akn/za/act/2014/10/import/', {
            'file': f,
            'expression_date': '2001-01-01',
            'language': '1'
        }, format='multipart')
        self.assertEqual(response.status_code, 200)

        # check the doc
        doc = work.expressions().filter(expression_date=datetime.date(2001, 1, 1)).first()
        self.assertEqual(doc.draft, True)
        self.assertIn('accreditation', doc.content, msg='"accreditation" missing')
        self.assertEqual(len(doc.attachments.all()), 2)

    def test_create_from_file(self):
        work = Work.objects.get_for_frbr_uri('/akn/za/act/1998/2')

        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt')
        tmp_file.write("""
        Chapter 2
        The Beginning
        1. First Verse
        (1) In the beginning
        (2) There was nothing
        """.encode())
        tmp_file.seek(0)
        fname = os.path.basename(tmp_file.name)

        response = self.client.post('/works/akn/za/act/1998/2/import/', {
            'file': tmp_file,
            'expression_date': '2001-01-01',
            'language': '1'
        }, format='multipart')
        self.assertEqual(response.status_code, 200)

        # check the doc
        doc = work.expressions().filter(expression_date=datetime.date(2001, 1, 1)).first()
        self.assertEqual(doc.draft, True)
        self.assertEqual(doc.title, 'Test Act')
        self.assertIn('In the beginning', doc.content)

        # check the attachment
        response = self.client.get('/api/documents/%s/attachments' % doc.id)
        self.assertEqual(response.status_code, 200)
        results = response.data['results']

        self.assertEqual(results[0]['mime_type'], 'text/plain')
        self.assertEqual(results[0]['filename'], fname)
        self.assertEqual(results[0]['url'], 'http://testserver/api/documents/%s/attachments/%s' % (doc.id, results[0]['id']))

        # test media view
        response = self.client.get('/api/documents/%s/media/%s' % (doc.id, fname))
        self.assertEqual(response.status_code, 200)

    def test_create_from_html(self):
        work = Work.objects.get_for_frbr_uri('/akn/za/act/2014/10')

        tmp_file = tempfile.NamedTemporaryFile(suffix='.html')
        # the \xc2\xa0 is an non-breaking space which should be changed to a normal space
        tmp_file.write(b"<div>a\xc2\xa0text file with <p>badly formed</div> HTML</p>")
        tmp_file.seek(0)

        response = self.client.post('/works/akn/za/act/2014/10/import/', {
            'file': tmp_file,
            'expression_date': '2001-01-01',
            'language': '1'
        }, format='multipart')
        self.assertEqual(response.status_code, 200)

        # check the doc
        doc = work.expressions().filter(expression_date=datetime.date(2001, 1, 1)).first()
        self.assertEqual(doc.draft, True)
        self.assertIn('a text file with badly formed</p><p>HTML', doc.content, msg='missing imported html')
        self.assertEqual(len(doc.attachments.all()), 1)

    def test_create_from_pdf_with_page_nums(self):
        work = Work.objects.get_for_frbr_uri('/akn/za/act/2014/10')

        fname = os.path.join(os.path.dirname(__file__), '../fixtures/sample.pdf')
        f = open(fname, 'rb')

        response = self.client.post('/works/akn/za/act/2014/10/import/', {
            'file': f,
            'expression_date': '2001-01-01',
            'page_nums': '2-3',
            'language': '1'
        }, format='multipart')
        self.assertEqual(response.status_code, 200)

        # check the doc
        doc = work.expressions().filter(expression_date=datetime.date(2001, 1, 1)).first()
        self.assertEqual(doc.draft, True)
        self.assertNotIn('first page', doc.content, msg='"first page" should not be included')
        self.assertIn('second page', doc.content, msg='"second page" missing')
        self.assertIn('third page', doc.content, msg='"third page" missing')
        self.assertNotIn('fourth page', doc.content, msg='"fourth page" should not be included')
        self.assertEqual(len(doc.attachments.all()), 1)

        # ensure the attachment only has 2 pages
        attachment = doc.attachments.first()
        pages = pdf_count_pages(attachment.file.name)
        self.assertEqual(pages, 2)
