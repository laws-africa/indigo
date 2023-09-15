from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from django.contrib.auth.models import User, Permission, ContentType

from indigo_api.models import Document, Annotation
from indigo_api.tests.fixtures import *  # noqa


class AnnotationAPITest(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'taxonomy_topics', 'work', 'drafts']

    def setUp(self):
        self.client.default_format = 'json'
        self.client.login(username='email@example.com', password='password')

    def test_new_annotation(self):
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor_id': 'section.1',
            'selectors': [{
                'type': 'TextPositionSelector',
                'start': 100,
                'end': 102,
            }],
        })

        assert_equal(response.status_code, 201)
        assert_equal(response.data['text'], 'hello')
        assert_equal(response.data['selectors'], [{
            'type': 'TextPositionSelector',
            'start': 100,
            'end': 102,
        }])
        assert_is_none(response.data['in_reply_to'])
        assert_is_not_none(response.data['created_by_user'])

    def test_reply(self):
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor_id': 'section.1',
        })

        assert_equal(response.status_code, 201)
        note_id = response.data['id']

        reply = self.client.post('/api/documents/10/annotations', {
            'text': 'reply',
            'anchor_id': 'section.1',
            'in_reply_to': note_id,
        })
        assert_equal(reply.status_code, 201)
        assert_equal(reply.data['in_reply_to'], note_id)

    def test_change(self):
        # create
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor_id': 'section.1',
        })
        note_id = response.data['id']

        # change
        resp2 = self.client.patch('/api/documents/10/annotations/%s' % note_id, {
            'text': 'updated',
            'anchor_id': 'different',
            'created_by_user': {'id': 99},
            'created_at': 'foo',
            'updated_at': 'bar',
        })
        assert_equal(resp2.status_code, 200)

        # verify
        resp3 = self.client.get('/api/documents/10/annotations/%s' % note_id)
        assert_equal(resp3.data['text'], 'updated')
        assert_equal(resp3.data['anchor_id'], 'different')
        assert_equal(resp3.data['created_by_user'], response.data['created_by_user'])

    def test_cant_change_different_owner(self):
        # create
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor_id': 'section.1',
        })
        note_id = response.data['id']

        # change user
        self.client.login(username='non-deleter@example.com', password='password')

        # change
        response = self.client.patch('/api/documents/10/annotations/%s' % note_id, {
            'text': 'goodbye',
        })
        assert_equal(response.status_code, 403)

    def test_cant_change_logged_out(self):
        # create
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor_id': 'section.1',
        })
        note_id = response.data['id']

        # change user
        self.client.logout()

        # change
        response = self.client.patch('/api/documents/10/annotations/%s' % note_id, {
            'text': 'goodbye',
        })
        assert_equal(response.status_code, 403)

    def test_create_annotation_task(self):
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor_id': 'sec_1',
        })

        assert_equal(response.status_code, 201)
        note_id = response.data['id']

        response = self.client.post('/api/documents/10/annotations/%s/task' % note_id)
        assert_equal(response.status_code, 201)
        assert_equal(response.data['title'], '"Section 1.": hello')
        assert_equal(response.data['state'], 'open')
        assert_is_none(response.data.get('anchor_id'))

    def test_create_annotation_task_anchor_missing(self):
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            # sec_99 doesn't exist
            'anchor_id': 'sec_99',
        })
        assert_equal(response.status_code, 201)
        note_id = response.data['id']

        response = self.client.post('/api/documents/10/annotations/%s/task' % note_id)
        assert_equal(response.status_code, 201)
        assert_equal(response.data['title'], '"sec_99": hello')
        assert_equal(response.data['state'], 'open')
        assert_is_none(response.data.get('anchor_id'))

    def test_annotation_permissions(self):
        self.client.logout()
        self.assertTrue(self.client.login(username='no-perms@example.com', password='password'))
        user = User.objects.get(username='no-perms@example.com')

        data = {
            'text': 'hello',
            'anchor_id': 'section.1',
            'selectors': [{
                'type': 'TextPositionSelector',
                'start': 100,
                'end': 102,
            }],
        }

        response = self.client.post('/api/documents/10/annotations', data)
        assert_equal(response.status_code, 403)

        # add view perms
        user.user_permissions.add(Permission.objects.get(
            codename='view_document',
            content_type=ContentType.objects.get_for_model(Document)
        ))

        response = self.client.post('/api/documents/10/annotations', data)
        assert_equal(response.status_code, 403)

        # add annotation add perms
        user.user_permissions.add(Permission.objects.get(
            codename='add_annotation',
            content_type=ContentType.objects.get_for_model(Annotation)
        ))

        response = self.client.post('/api/documents/10/annotations', data)
        assert_equal(response.status_code, 201)
