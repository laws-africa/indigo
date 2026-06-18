import tempfile
from unittest.mock import patch
import datetime

from rest_framework.test import APITestCase
from django.test.utils import override_settings
from django.core.files.base import ContentFile

from indigo_api.tests.fixtures import *  # noqa
from indigo_api.exporters import PDFExporter
from indigo_api.models import Work, Attachment
from indigo_app.tests.utils import TEST_STORAGES


@override_settings(STORAGES=TEST_STORAGES)
class DocumentAPITest(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomy_topics', 'work', 'colophon', 'drafts', 'published', 'attachments']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')

    def test_update_title_overrides_content_xml(self):
        response = self.client.patch('/api/documents/1', {
            'content': document_fixture('in the body'),
            'title': 'Document title',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Document title')

        response = self.client.get('/api/documents/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Document title')

    def test_update_expression_date(self):
        id = 1
        response = self.client.patch('/api/documents/%s' % id, {'expression_date': '2015-01-01'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['expression_date'], '2015-01-01')

        response = self.client.get('/api/documents/%s' % id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['expression_date'], '2015-01-01')

    def test_update_content(self):
        id = 1
        revisions1 = self.client.get('/api/documents/%s/revisions' % id).data
        response = self.client.patch('/api/documents/%s' % id, {'content': document_fixture('in γνωρίζω body')})
        self.assertEqual(response.status_code, 200)
        revisions2 = self.client.get('/api/documents/%s/revisions' % id).data

        # ensure a revision is created
        self.assertNotEqual(revisions1, revisions2, 'revision not created')

        response = self.client.get('/api/documents/%s/content' % id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<p>in γνωρίζω body</p>', response.data['content'])

    def test_revert_a_revision(self):
        id = 1
        response = self.client.patch('/api/documents/%s' % id, {'content': document_fixture('hello in there')})
        self.assertEqual(response.status_code, 200)
        response = self.client.patch('/api/documents/%s' % id, {'content': document_fixture('goodbye')})
        self.assertEqual(response.status_code, 200)

        revisions = self.client.get('/api/documents/%s/revisions' % id).data
        self.assertEqual(response.status_code, 200)
        revision_id = revisions['results'][1]['id']

        response = self.client.post('/api/documents/%s/revisions/%s/restore' % (id, revision_id))
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/documents/%s/content' % id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<p>hello in there</p>', response.data['content'])

    def test_get_a_revision_diff(self):
        id = 1
        response = self.client.patch('/api/documents/%s' % id, {'content': document_fixture('hello')})
        self.assertEqual(response.status_code, 200)
        response = self.client.patch('/api/documents/%s' % id, {'content': document_fixture('goodbye')})
        self.assertEqual(response.status_code, 200)

        revisions = self.client.get('/api/documents/%s/revisions' % id).data
        self.assertEqual(response.status_code, 200)
        revision_id = revisions['results'][1]['id']

        response = self.client.get('/api/documents/%s/revisions/%s/diff' % (id, revision_id))
        self.assertEqual(response.status_code, 200)

    def test_update_content_and_properties(self):
        response = self.client.patch('/api/documents/1', {
            'content': document_fixture('in γνωρίζω body'),
            'title': 'the title'})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/documents/1/content')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<p>in γνωρίζω body</p>', response.data['content'])

        response = self.client.get('/api/documents/1')
        self.assertEqual(response.data['title'], 'the title')

    def test_delete(self):
        response = self.client.delete('/api/documents/10')
        self.assertEqual(response.status_code, 204)

    def test_cannot_delete(self):
        # this user cannot delete
        self.client.login(username='non-deleter@example.com', password='password')
        response = self.client.delete('/api/documents/10')
        self.assertEqual(response.status_code, 403)

    def test_cannot_publish(self):
        # this user cannot publish
        self.client.login(username='non-publisher@example.com', password='password')
        response = self.client.patch('/api/documents/10', {'draft': False})
        self.assertEqual(response.status_code, 403)

    def test_cannot_unpublish(self):
        # this user cannot unpublish
        self.client.login(username='non-publisher@example.com', password='password')
        response = self.client.patch('/api/documents/1', {'draft': False})
        self.assertEqual(response.status_code, 403)

    def test_cannot_update_published(self):
        # this user cannot edit published
        self.client.login(username='non-publisher@example.com', password='password')
        response = self.client.patch('/api/documents/1', {'title': 'A new title'})
        self.assertEqual(response.status_code, 403)

    def test_table_of_contents(self):
        xml = """
          <chapter eId="chapter-2">
            <num>2</num>
            <heading>Administrative provisions</heading>
            <section eId="section-3">
              <num>3.</num>
              <heading>Consent required for <term refersTo="#term-interment" eId="trm80">interment</term></heading>
              <subsection eId="section-3.1">
                <num>(1)</num>
                <content><p>hello</p></content>
              </subsection>
            </section>
          </chapter>
        """

        response = self.client.patch('/api/documents/1', {
            'content': document_fixture(xml=xml),
        })
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/documents/1/toc')
        self.assertEqual(response.status_code, 200)

        self.maxDiff = None
        # toc now includes `subsection`
        self.assertEqual([
            {
                'type': 'chapter',
                'num': '2',
                'heading': 'Administrative provisions',
                'id': 'chapter-2',
                'component': 'main',
                'title': 'Chapter 2 – Administrative provisions',
                'basic_unit': False,
                'children': [
                    {
                        'type': 'section',
                        'num': '3.',
                        'heading': 'Consent required for interment',
                        'id': 'section-3',
                        'title': '3. Consent required for interment',
                        'component': 'main',
                        'basic_unit': True,
                        'children': [
                            {
                                'type': 'subsection',
                                'component': 'main',
                                'title': 'Subsection (1)',
                                'num': '(1)',
                                'id': 'section-3.1',
                                'basic_unit': False,
                                'children': [],
                                'heading': None,
                            }
                        ]
                    },
                ],
            },
        ], response.data['toc'])

    def test_attachment_as_media(self):
        id = 1

        # not created yet
        response = self.client.get('/api/documents/%s/media/test.txt' % id)
        self.assertEqual(response.status_code, 404)

        # create it
        # create a doc with an attachment
        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt')
        tmp_file.write("hello!".encode())
        tmp_file.seek(0)
        response = self.client.post('/api/documents/%s/attachments' % id,
                                    {'file': tmp_file, 'filename': 'test.txt'}, format='multipart')
        self.assertEqual(response.status_code, 201)

        # now should exist
        response = self.client.get('/api/documents/%s/media/test.txt' % id)
        self.assertEqual(response.status_code, 200)

    def test_attachment_as_media_anonymous(self):
        id = 1

        # create it
        # create a doc with an attachment
        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt')
        tmp_file.write("hello!".encode())
        tmp_file.seek(0)
        response = self.client.post('/api/documents/%s/attachments' % id,
                                    {'file': tmp_file, 'filename': 'test.txt'}, format='multipart')
        self.assertEqual(response.status_code, 201)

        # now should exist
        response = self.client.get('/api/documents/%s/media/test.txt' % id)
        self.assertEqual(response.status_code, 200)

        # not allowed
        self.client.logout()
        response = self.client.get('/api/documents/%s/media/test.txt' % id)
        self.assertEqual(response.status_code, 403)

    def test_update_attachment(self):
        # create an attachment for a doc
        work = Work.objects.get_for_frbr_uri('/akn/za/act/2014/10')
        doc = work.expressions().first()

        attachment = Attachment(document=doc)
        attachment.filename = "foo.txt"
        attachment.size = 100
        attachment.mime_type = "text/plain"
        attachment.file.save("foo.txt", ContentFile("foo"))
        attachment.save()

        # check the attachment
        response = self.client.get('/api/documents/%s/attachments' % doc.id)
        self.assertEqual(response.status_code, 200)
        data = response.data['results'][0]
        self.assertEqual(data['mime_type'], 'text/plain')

        # test patch
        data['filename'] = 'new.txt'
        response = self.client.patch(data['url'], data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['filename'], 'new.txt')

        # test put
        response = self.client.put(data['url'], {'filename': 'new-from-patch.txt'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['filename'], 'new-from-patch.txt')

        # test put with slashes in filename
        response = self.client.put(data['url'], {'filename': '/with/slashes.txt'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['filename'], 'withslashes.txt')

    @patch.object(PDFExporter, 'render', return_value='pdf-content')
    def test_document_pdf(self, mock):
        response = self.client.get('/api/documents/1.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/pdf')
        self.assertIn('pdf-content', response.content.decode('utf-8'))

    def test_document_xml(self):
        response = self.client.get('/api/documents/1.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/xml')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=2014-10.xml')
        self.assertTrue(response.content.decode('utf-8').startswith('<akomaNtoso'))

    def test_document_epub(self):
        response = self.client.get('/api/documents/1.epub')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/epub+zip')
        self.assertTrue(response.content.startswith(b'PK'))

    def test_document_pdf_404(self):
        response = self.client.get('/api/documents/999.pdf')
        self.assertEqual(response.status_code, 404)

    def test_document_epub_404(self):
        response = self.client.get('/api/documents/999.epub')
        self.assertEqual(response.status_code, 404)

    def test_document_standalone_html(self):
        response = self.client.get('/api/documents/1.html?standalone=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'text/html')
        self.assertNotIn('<akomaNtoso', response.content.decode('utf-8'))
        self.assertIn('<body  class="standalone"', response.content.decode('utf-8'))
        self.assertIn('class="colophon"', response.content.decode('utf-8'))
        self.assertIn('class="toc"', response.content.decode('utf-8'))

    def test_document_html(self):
        response = self.client.get('/api/documents/1.html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'text/html')
        self.assertNotIn('<akomaNtoso', response.content.decode('utf-8'))
        self.assertNotIn('<body  class="standalone"', response.content.decode('utf-8'))
        self.assertNotIn('class="colophon"', response.content.decode('utf-8'))
        self.assertNotIn('class="toc"', response.content.decode('utf-8'))
        self.assertIn('<div ', response.content.decode('utf-8'))

    def test_published_html_l10n(self):
        response = self.client.patch('/api/documents/1', {'language': 'afr'})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/documents/1.html')
        self.assertEqual(response.accepted_media_type, 'text/html')
        self.assertNotIn('<akomaNtoso', response.content.decode('utf-8'))
        self.assertIn('<div', response.content.decode('utf-8'))
        self.assertIn('Wet 10 van 2014', response.content.decode('utf-8'))

    def test_document_zipfile(self):
        response = self.client.get('/api/documents/1.zip')
        self.assertEqual(response.accepted_media_type, 'application/zip')

    def test_update_work_repeal(self):
        work = Work.objects.get(pk=1)
        work.repealed_by = Work.objects.get(pk=2)
        work.repealed_date = datetime.date(2010, 1, 1)
        work.save()

        response = self.client.get('/api/documents/1')
        self.assertEqual(response.data['repeal'], {
            'date': '2010-01-01',
            'repealing_title': 'Test Act',
            'repealing_uri': '/akn/za/act/1998/2',
        })
