# -*- coding: utf8 -*-

import tempfile
import os.path
from mock import patch

from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from django.test.utils import override_settings

from indigo_api.tests.fixtures import *  # noqa
from indigo_api.renderers import PDFRenderer


# Disable pipeline storage - see https://github.com/cyberdelia/django-pipeline/issues/277
@override_settings(STATICFILES_STORAGE='pipeline.storage.PipelineStorage', PIPELINE_ENABLED=False)
class DocumentAPITest(APITestCase):
    fixtures = ['user', 'colophon']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')

    def test_simple_create(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2'
        })

        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za/act/1998/2')
        assert_equal(response.data['title'], '(untitled)')
        assert_equal(response.data['nature'], 'act')
        assert_equal(response.data['year'], '1998')
        assert_equal(response.data['number'], '2')
        assert_equal(response.data['amendments'], [])
        assert_equal(response.data['amended_versions'], [])

        # these should not be included directly, they should have URLs
        id = response.data['id']
        assert_not_in('content', response.data)
        assert_not_in('toc', response.data)
        assert_equal(response.data['content_url'], 'http://testserver/api/documents/%s/content' % id)
        assert_equal(response.data['toc_url'], 'http://testserver/api/documents/%s/toc' % id)

        response = self.client.get('/api/documents/%s/content' % response.data['id'])
        assert_equal(response.status_code, 200)

        assert_in('<p/>', response.data['content'])

    def test_create_with_tags(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'tags': ['foo', 'bar']
        })

        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za/act/1998/2')
        assert_equal(response.data['draft'], True)
        assert_equal(sorted(response.data['tags']), ['bar', 'foo'])

    def test_create_with_locality(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za-cpt/act/1998/2',
            'draft': False,
        })

        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za-cpt/act/1998/2')

        response = self.client.get('/api/za-cpt/act/1998/2')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['frbr_uri'], '/za-cpt/act/1998/2')

    def test_create_title_overrides_content_xml(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za-cpt/act/1998/2',
            'content': document_fixture('in the body'),
            'title': 'Document title',
            'draft': True,
            'tags': ['a'],
        })
        id = response.data['id']

        assert_equal(response.status_code, 201)
        assert_equal(response.data['title'], 'Document title')

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['title'], 'Document title')
        assert_equal(response.data['frbr_uri'], '/za-cpt/act/1998/2')

    def test_update(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'tags': ['foo', 'bar']})
        assert_equal(response.status_code, 200)
        assert_equal(sorted(response.data['tags']), ['bar', 'foo'])

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(sorted(response.data['tags']), ['bar', 'foo'])

    def test_update_tags(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'tags': ['foo', 'bar']})
        assert_equal(response.status_code, 200)
        assert_equal(sorted(response.data['tags']), ['bar', 'foo'])

        response = self.client.patch('/api/documents/%s' % id, {'tags': ['boom', 'bar']})
        assert_equal(response.status_code, 200)
        assert_equal(sorted(response.data['tags']), ['bar', 'boom'])

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(sorted(response.data['tags']), ['bar', 'boom'])

    def test_update_publication_date(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'publication_date': '2015-01-01'})
        assert_equal(response.status_code, 200)
        assert_equal(response.data['publication_date'], '2015-01-01')

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['publication_date'], '2015-01-01')

    def test_update_expression_date(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'expression_date': '2015-01-01'})
        assert_equal(response.status_code, 200)
        assert_equal(response.data['expression_date'], '2015-01-01')

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['expression_date'], '2015-01-01')

    def test_update_content(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        revisions1 = self.client.get('/api/documents/%s/revisions' % id).data
        response = self.client.patch('/api/documents/%s' % id, {'content': document_fixture(u'in γνωρίζω body')})
        assert_equal(response.status_code, 200)
        revisions2 = self.client.get('/api/documents/%s/revisions' % id).data

        # ensure a revision is created
        assert_not_equal(revisions1, revisions2, 'revision not created')

        response = self.client.get('/api/documents/%s/content' % id)
        assert_equal(response.status_code, 200)
        assert_in(u'<p>in γνωρίζω body</p>', response.data['content'])

        # also try updating the content at /content
        response = self.client.put('/api/documents/%s/content' % id, {'content': document_fixture(u'also γνωρίζω the body')})
        assert_equal(response.status_code, 200)
        revisions3 = self.client.get('/api/documents/%s/revisions' % id).data

        # ensure a revision is created
        assert_not_equal(revisions2, revisions3, 'revision not created')

        response = self.client.get('/api/documents/%s/content' % id)
        assert_equal(response.status_code, 200)
        assert_in(u'<p>also γνωρίζω the body</p>', response.data['content'])

    def test_revert_a_revision(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2', 'content': document_fixture(u'hello in there')})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'content': document_fixture(u'goodbye')})
        assert_equal(response.status_code, 200)

        revisions = self.client.get('/api/documents/%s/revisions' % id).data
        revision_id = revisions['results'][1]['id']

        response = self.client.post('/api/documents/%s/revisions/%s/restore' % (id, revision_id))
        assert_equal(response.status_code, 200)

        response = self.client.get('/api/documents/%s/content' % id)
        assert_equal(response.status_code, 200)
        assert_in(u'<p>hello in there</p>', response.data['content'])

    def test_get_a_revision_diff(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2', 'content': document_fixture(u'hello in there')})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'content': document_fixture(u'goodbye')})
        assert_equal(response.status_code, 200)

        revisions = self.client.get('/api/documents/%s/revisions' % id).data
        revision_id = revisions['results'][1]['id']

        response = self.client.get('/api/documents/%s/revisions/%s/diff' % (id, revision_id))
        assert_equal(response.status_code, 200)

    def test_update_content_and_properties(self):
        # ensure properties override content
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']
        assert_equal(response.data['title'], '(untitled)')

        response = self.client.patch('/api/documents/%s' % id, {
            'content': document_fixture(u'in γνωρίζω body'),
            'title': 'the title'})
        assert_equal(response.status_code, 200)

        response = self.client.get('/api/documents/%s/content' % id)
        assert_equal(response.status_code, 200)
        assert_in(u'<p>in γνωρίζω body</p>', response.data['content'])

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.data['title'], 'the title')

    def test_frbr_uri_lowercased(self):
        # ACT should be changed to act
        response = self.client.post('/api/documents', {'frbr_uri': '/za/ACT/1998/2'})
        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za/act/1998/2')

    def test_create_with_content(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'content': document_fixture('in the body'),
        })
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.get('/api/documents/%s/content' % id)
        assert_equal(response.status_code, 200)
        assert_in('<p>in the body</p>', response.data['content'])

    def test_create_with_bad_content(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'content': 'not valid xml',
        })
        assert_equal(response.status_code, 400)
        assert_equal(len(response.data['content']), 1)

    def test_create_with_bad_uri(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/',
            'content': document_fixture('in the body'),
        })
        assert_equal(response.status_code, 400)
        assert_equal(len(response.data['frbr_uri']), 1)

    def test_delete(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.delete('/api/documents/%s' % id)
        assert_equal(response.status_code, 204)

    def test_cannot_delete(self):
        # this user cannot delete
        self.client.login(username='non-deleter@example.com', password='password')

        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.delete('/api/documents/%s' % id)
        assert_equal(response.status_code, 403)

    def test_cannot_publish(self):
        # this user cannot publish
        self.client.login(username='non-publisher@example.com', password='password')

        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.put('/api/documents/%s' % id, {'draft': False})
        assert_equal(response.status_code, 403)

    def test_cannot_unpublish(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2', 'draft': False})
        assert_equal(response.status_code, 201)
        id = response.data['id']
        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.data['draft'], False)

        # this user cannot unpublish
        self.client.login(username='non-publisher@example.com', password='password')
        response = self.client.put('/api/documents/%s' % id, {'draft': True})
        assert_equal(response.status_code, 403)

    def test_cannot_update_published(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2', 'draft': False})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        # this user cannot edit published
        self.client.login(username='non-publisher@example.com', password='password')
        response = self.client.put('/api/documents/%s' % id, {'title': 'A new title'})
        assert_equal(response.status_code, 403)

    def test_table_of_contents(self):
        xml = """
          <chapter id="chapter-2">
            <num>2</num>
            <heading>Administrative provisions</heading>
            <section id="section-3">
              <num>3.</num>
              <heading>Consent required for <term refersTo="#term-interment" id="trm80">interment</term></heading>
              <subsection id="section-3.1">
                <num>(1)</num>
                <content><p>hello</p></content>
              </subsection>
            </section>
          </chapter>
        """

        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'content': document_fixture(xml=xml),
        })
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.get('/api/documents/%s/toc' % id)
        assert_equal(response.status_code, 200)

        self.maxDiff = None
        self.assertEqual(response.data['toc'], [
            {
                'type': 'chapter',
                'num': '2',
                'heading': 'Administrative provisions',
                'id': 'chapter-2',
                'component': 'main',
                'title': 'Chapter 2 - Administrative provisions',
                'subcomponent': 'chapter/2',
                'url': 'http://testserver/api/za/act/1998/2/eng/main/chapter/2',
                'children': [
                    {
                        'type': 'section',
                        'num': '3.',
                        'heading': 'Consent required for interment',
                        'id': 'section-3',
                        'title': '3. Consent required for interment',
                        'component': 'main',
                        'subcomponent': 'section/3',
                        'url': 'http://testserver/api/za/act/1998/2/eng/main/section/3',
                    },
                ],
            },
        ])

    def test_create_with_amendments(self):
        # this document made the amendments
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/2010/2',
            'expression_date': '2010-01-01',
        })
        assert_equal(response.status_code, 201)
        amending_id = response.data['id']
        assert_is_not_none(amending_id)

        # this is the amended document
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'amendments': [{
                'date': '2010-01-01',
                'amending_title': 'Act 2 of 2010',
                'amending_uri': '/za/act/2010/2',
            }]
        })
        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za/act/1998/2')
        assert_equal(response.data['amendments'], [{
            'date': '2010-01-01',
            'amending_title': 'Act 2 of 2010',
            'amending_uri': '/za/act/2010/2',
            'amending_id': amending_id,
        }])

        # ensure it shows amending_id when listed
        response = self.client.get('/api/documents')
        assert_equal(response.status_code, 200)
        doc = list(d for d in response.data['results'] if d['frbr_uri'] == '/za/act/1998/2')[0]
        assert_equal(doc['amendments'], [{
            'date': '2010-01-01',
            'amending_title': 'Act 2 of 2010',
            'amending_uri': '/za/act/2010/2',
            'amending_id': amending_id,
        }])

    def test_update_with_amendments(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {
            'amendments': [{
                'date': '2010-01-01',
                'amending_title': 'Act 2 of 2010',
                'amending_uri': '/za/act/2010/2',
            }]
        })

        assert_equal(response.status_code, 200)
        assert_equal(response.data['amendments'], [{
            'date': '2010-01-01',
            'amending_title': 'Act 2 of 2010',
            'amending_uri': '/za/act/2010/2',
            'amending_id': None,
        }])

    def test_update_with_repeal(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {
            'repeal': {
                'date': '2010-01-01',
                'repealing_title': 'Act 2 of 2010',
                'repealing_uri': '/za/act/2010/2',
            }
        })

        assert_equal(response.status_code, 200)
        assert_equal(response.data['repeal'], {
            'date': '2010-01-01',
            'repealing_title': 'Act 2 of 2010',
            'repealing_uri': '/za/act/2010/2',
            'repealing_id': None,
        })

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['repeal'], {
            'date': '2010-01-01',
            'repealing_title': 'Act 2 of 2010',
            'repealing_uri': '/za/act/2010/2',
            'repealing_id': None,
        })

    def test_update_null_repeal(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {
            'repeal': None,
        })

        assert_equal(response.status_code, 200)
        assert_equal(response.data['repeal'], None)

    def test_create_from_file(self):
        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt')
        tmp_file.write("""
        Chapter 2
        The Beginning
        1. First Verse
        (1) In the beginning
        (2) There was nothing
        """)
        tmp_file.seek(0)

        response = self.client.post('/api/documents', {'file': tmp_file}, format='multipart')
        assert_equal(response.status_code, 201)
        id = response.data['id']

        # check the doc
        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.data['draft'], True)
        assert_not_equal(response.data['frbr_uri'], '/za/act/1980/01')

        # check the attachment
        response = self.client.get('/api/documents/%s/attachments' % id)
        assert_equal(response.status_code, 200)
        results = response.data['results']

        assert_equal(results[0]['mime_type'], 'text/plain')
        assert_equal(results[0]['filename'], os.path.basename(tmp_file.name))
        assert_equal(results[0]['url'],
                     'http://testserver/api/documents/%s/attachments/%s' % (id, results[0]['id']))

    def test_update_attachment(self):
        # create a doc with an attachment
        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt')
        tmp_file.write("""
        Chapter 2
        The Beginning
        1. First Verse
        (1) In the beginning
        (2) There was nothing
        """)
        tmp_file.seek(0)

        response = self.client.post('/api/documents', {'file': tmp_file}, format='multipart')
        assert_equal(response.status_code, 201)
        id = response.data['id']

        # check the attachment
        response = self.client.get('/api/documents/%s/attachments' % id)
        assert_equal(response.status_code, 200)
        data = response.data['results'][0]
        assert_equal(data['mime_type'], 'text/plain')

        # test patch
        data['filename'] = 'new.txt'
        response = self.client.patch(data['url'], data)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['filename'], 'new.txt')

        # test put
        response = self.client.put(data['url'], {'filename': 'new-from-patch.txt'})
        assert_equal(response.status_code, 200)
        assert_equal(response.data['filename'], 'new-from-patch.txt')

        # test put with slashes in filename
        response = self.client.put(data['url'], {'filename': '/with/slashes.txt'})
        assert_equal(response.status_code, 200)
        assert_equal(response.data['filename'], 'withslashes.txt')

    @patch.object(PDFRenderer, '_wkhtmltopdf', return_value='pdf-content')
    def test_document_pdf(self, mock):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.get('/api/documents/%s.pdf' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/pdf')
        assert_in('pdf-content', response.content)

    def test_document_epub(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.get('/api/documents/%s.epub' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/epub+zip')
        assert_true(response.content.startswith('PK'))

    def test_document_pdf_404(self):
        response = self.client.get('/api/documents/999.pdf')
        assert_equal(response.status_code, 404)

    def test_document_epub_404(self):
        response = self.client.get('/api/documents/999.epub')
        assert_equal(response.status_code, 404)

    def test_document_standalone_html(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.get('/api/documents/%s.html?standalone=1' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'text/html')
        assert_not_in('<akomaNtoso', response.content)
        assert_in('<body  class="standalone"', response.content)
        assert_in('class="colophon"', response.content)
        assert_in('class="toc"', response.content)

    def test_document_html(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.get('/api/documents/%s.html' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'text/html')
        assert_not_in('<akomaNtoso', response.content)
        assert_not_in('<body  class="standalone"', response.content)
        assert_not_in('class="colophon"', response.content)
        assert_not_in('class="toc"', response.content)
        assert_in('<div ', response.content)
