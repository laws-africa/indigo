import tempfile
from unittest.mock import patch
import datetime
import uuid

from rest_framework.test import APITestCase
from rest_framework import serializers
from django.contrib.auth.models import Permission, User
from django.test.utils import override_settings
from django.core.files.base import ContentFile
from django.utils import timezone

from indigo_api.tests.fixtures import *  # noqa
from indigo_api.exporters import PDFExporter
from indigo_api.models import Work, Attachment, Country, Document, DocumentEditLease
from indigo_app.tests.utils import TEST_STORAGES


@override_settings(STORAGES=TEST_STORAGES)
class DocumentAPITest(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomy_topics', 'work', 'colophon', 'drafts', 'published', 'attachments']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')
        source_document = Document.objects.get(pk=10)
        other_work = Work.objects.create(
            title='Restricted Namibia Act',
            country=Country.objects.get(country_id='NA'),
            frbr_uri='/akn/na/act/2026/1',
            doctype='act',
            date='2026',
            number='1',
        )
        self.restricted_document = Document.objects.create(
            title='Restricted Namibia draft',
            frbr_uri='/akn/na/act/2026/1',
            work=other_work,
            expression_date=datetime.date(2026, 1, 1),
            language=source_document.language,
            draft=True,
            document_xml=source_document.document_xml,
            created_by_user=source_document.created_by_user,
            updated_by_user=source_document.updated_by_user,
        )

    def test_cannot_read_documents_from_another_country(self):
        document_id = self.restricted_document.id

        for url in [
            f'/api/documents/{document_id}',
            f'/api/documents/{document_id}/content',
            f'/api/documents/{document_id}.xml',
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, url)

        response = self.client.get('/api/documents')
        self.assertNotIn(document_id, [document['id'] for document in response.data['results']])

        # Document-linked resources must enforce the same country scope.
        response = self.client.get(f'/api/documents/{document_id}/annotations')
        self.assertEqual(response.status_code, 403)

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

    def test_update_with_matching_expected_updated_at(self):
        document = self.client.get('/api/documents/1').data

        response = self.client.patch('/api/documents/1', {
            'expected_updated_at': document['updated_at'],
            'title': 'Updated safely',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Updated safely')
        self.assertNotEqual(response.data['updated_at'], document['updated_at'])

    def test_stale_update_does_not_overwrite_document(self):
        original = self.client.get('/api/documents/1').data
        first_response = self.client.patch('/api/documents/1', {
            'expected_updated_at': original['updated_at'],
            'title': 'First editor won',
        })
        self.assertEqual(first_response.status_code, 200)
        revisions_after_first_save = self.client.get('/api/documents/1/revisions').data

        stale_response = self.client.patch('/api/documents/1', {
            'expected_updated_at': original['updated_at'],
            'title': 'Stale editor overwrote it',
            'content': document_fixture('stale content'),
        })

        self.assertEqual(stale_response.status_code, 409)
        self.assertEqual(stale_response.data['code'], 'document_changed')
        self.assertEqual(stale_response.data['expected_updated_at'], original['updated_at'])
        self.assertEqual(
            stale_response.data['current_updated_at'],
            first_response.data['updated_at'],
        )
        self.assertEqual(
            stale_response.data['updated_by_user']['id'],
            first_response.data['updated_by_user']['id'],
        )

        current = self.client.get('/api/documents/1').data
        self.assertEqual(current['title'], 'First editor won')
        content = self.client.get('/api/documents/1/content').data['content']
        self.assertNotIn('stale content', content)
        self.assertEqual(
            self.client.get('/api/documents/1/revisions').data,
            revisions_after_first_save,
        )

    def acquire_edit_lease(self, document_id=10, **overrides):
        document = self.client.get(f'/api/documents/{document_id}').data
        data = {
            'expected_updated_at': document['updated_at'],
            'client_id': str(uuid.uuid4()),
            'activity_nonce': str(uuid.uuid4())[:10],
        }
        data.update(overrides)
        return self.client.post(f'/api/documents/{document_id}/edit-lease', data), document

    def test_acquire_and_renew_edit_lease(self):
        response, document = self.acquire_edit_lease()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['document_updated_at'], document['updated_at'])
        self.assertEqual(
            response.data['activity_nonce'],
            DocumentEditLease.objects.get(document_id=10).activity_nonce,
        )

        renewed = self.client.post('/api/documents/10/edit-lease', {
            'expected_updated_at': document['updated_at'],
            'client_id': response.data['client_id'],
            'activity_nonce': 'new-page',
            'token': response.data['token'],
        })
        self.assertEqual(renewed.status_code, 200)
        self.assertEqual(renewed.data['token'], response.data['token'])
        self.assertEqual(renewed.data['activity_nonce'], 'new-page')

    def test_release_edit_lease(self):
        response, _ = self.acquire_edit_lease()

        released = self.client.post('/api/documents/10/edit-lease/release', {
            'client_id': response.data['client_id'],
            'token': response.data['token'],
        })

        self.assertEqual(released.status_code, 204)
        self.assertFalse(DocumentEditLease.objects.filter(document_id=10).exists())

        # Repeated releases are harmless.
        released = self.client.post('/api/documents/10/edit-lease/release', {
            'client_id': response.data['client_id'],
            'token': response.data['token'],
        })
        self.assertEqual(released.status_code, 204)

    def test_release_does_not_delete_another_clients_lease(self):
        response, _ = self.acquire_edit_lease()

        released = self.client.post('/api/documents/10/edit-lease/release', {
            'client_id': str(uuid.uuid4()),
            'token': response.data['token'],
        })

        self.assertEqual(released.status_code, 204)
        self.assertTrue(DocumentEditLease.objects.filter(document_id=10).exists())

    def test_document_activity_identifies_edit_lease_holder(self):
        user = User.objects.get(username='email@example.com')
        user.user_permissions.add(*Permission.objects.filter(
            codename__in=('add_documentactivity', 'view_documentactivity'),
        ))
        activity_url = '/api/documents/10/activity'
        response = self.client.post(activity_url, {'nonce': 'lease-test'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['results'][0]['has_edit_lease'])
        self.client.post(activity_url, {'nonce': 'other-tab'})

        lease, _ = self.acquire_edit_lease(10, activity_nonce='lease-test')
        self.assertEqual(lease.status_code, 200)
        response = self.client.post(activity_url, {'nonce': 'lease-test'})

        self.assertEqual(response.status_code, 200)
        activities = {activity['nonce']: activity for activity in response.data['results']}
        self.assertTrue(activities['lease-test']['has_edit_lease'])
        self.assertFalse(activities['other-tab']['has_edit_lease'])

    def test_second_client_cannot_acquire_active_lease(self):
        first, document = self.acquire_edit_lease()
        self.assertEqual(first.status_code, 200)

        second, _ = self.acquire_edit_lease(
            expected_updated_at=document['updated_at'],
            client_id=str(uuid.uuid4()),
        )
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.data['code'], 'document_locked')
        self.assertEqual(second.data['holder']['id'], first.data['holder']['id'])

    def test_stale_client_cannot_acquire_or_reacquire_lease(self):
        lease_response, document = self.acquire_edit_lease()
        lease = DocumentEditLease.objects.get(document_id=10)
        lease.expires_at = timezone.now() - datetime.timedelta(seconds=1)
        lease.save(update_fields=('expires_at',))

        self.client.patch('/api/documents/10', {'title': 'Changed elsewhere'})
        stale = self.client.post('/api/documents/10/edit-lease', {
            'expected_updated_at': document['updated_at'],
            'client_id': lease_response.data['client_id'],
            'token': lease_response.data['token'],
        })
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.data['code'], 'document_changed')

    def test_current_client_can_reacquire_expired_lease(self):
        lease_response, document = self.acquire_edit_lease()
        lease = DocumentEditLease.objects.get(document_id=10)
        lease.expires_at = timezone.now() - datetime.timedelta(seconds=1)
        lease.save(update_fields=('expires_at',))

        reacquired = self.client.post('/api/documents/10/edit-lease', {
            'expected_updated_at': document['updated_at'],
            'client_id': lease_response.data['client_id'],
            'token': lease_response.data['token'],
        })
        self.assertEqual(reacquired.status_code, 200)
        self.assertEqual(reacquired.data['token'], lease_response.data['token'])
        self.assertGreater(DocumentEditLease.objects.get(document_id=10).expires_at, timezone.now())

    def test_save_with_lease_advances_lease_version(self):
        lease_response, document = self.acquire_edit_lease()

        saved = self.client.patch('/api/documents/10', {
            'expected_updated_at': document['updated_at'],
            'edit_lease_token': lease_response.data['token'],
            'title': 'Saved under lease',
        })
        self.assertEqual(saved.status_code, 200)

        lease = DocumentEditLease.objects.get(document_id=10)
        self.assertEqual(lease.document_updated_at, Document.objects.get(pk=10).updated_at)
        self.assertEqual(
            serializers.DateTimeField().to_representation(lease.document_updated_at),
            saved.data['updated_at'],
        )

    def test_save_with_expired_lease_is_rejected(self):
        lease_response, document = self.acquire_edit_lease()
        lease = DocumentEditLease.objects.get(document_id=10)
        lease.expires_at = timezone.now() - datetime.timedelta(seconds=1)
        lease.save(update_fields=('expires_at',))

        response = self.client.patch('/api/documents/10', {
            'expected_updated_at': document['updated_at'],
            'edit_lease_token': lease_response.data['token'],
            'title': 'Must not save',
        })
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'edit_lease_lost')
        self.assertNotEqual(Document.objects.get(pk=10).title, 'Must not save')

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
        self.assertIn('private', response['Cache-Control'])
        self.assertNotIn('public', response['Cache-Control'])

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

    def test_attachment_mutation_with_edit_lease(self):
        document = self.client.get('/api/documents/10').data
        lease, _ = self.acquire_edit_lease(10)
        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt')
        tmp_file.write(b'leased attachment')
        tmp_file.seek(0)

        response = self.client.post(
            '/api/documents/10/attachments',
            {'file': tmp_file, 'filename': 'leased.txt'},
            format='multipart',
            HTTP_X_EDIT_LEASE_TOKEN=lease.data['token'],
            HTTP_X_EXPECTED_UPDATED_AT=document['updated_at'],
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Attachment.objects.filter(document_id=10, filename='leased.txt').exists())

    def test_attachment_mutation_rejects_expired_edit_lease(self):
        document = self.client.get('/api/documents/10').data
        lease, _ = self.acquire_edit_lease(10)
        DocumentEditLease.objects.filter(document_id=10).update(
            expires_at=timezone.now() - datetime.timedelta(seconds=1),
        )
        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt')
        tmp_file.write(b'should not be saved')
        tmp_file.seek(0)

        response = self.client.post(
            '/api/documents/10/attachments',
            {'file': tmp_file, 'filename': 'rejected.txt'},
            format='multipart',
            HTTP_X_EDIT_LEASE_TOKEN=lease.data['token'],
            HTTP_X_EXPECTED_UPDATED_AT=document['updated_at'],
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'edit_lease_lost')
        self.assertFalse(Attachment.objects.filter(document_id=10, filename='rejected.txt').exists())

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
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="2014-10.xml"')
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
