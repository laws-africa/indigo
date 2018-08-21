# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase

from indigo_api.tests.fixtures import *  # noqa


class AnnotationAPITest(APITestCase):
    fixtures = ['countries', 'user', 'editor', 'work', 'drafts']

    def setUp(self):
        self.client.default_format = 'json'
        self.client.login(username='email@example.com', password='password')

    def test_new_annotation(self):
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor': {'id': 'section.1'},
        })

        assert_equal(response.status_code, 201)
        assert_equal(response.data['text'], 'hello')
        assert_is_none(response.data['in_reply_to'])
        assert_is_not_none(response.data['created_by_user'])

    def test_reply(self):
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor': {'id': 'section.1'},
        })

        assert_equal(response.status_code, 201)
        note_id = response.data['id']

        reply = self.client.post('/api/documents/10/annotations', {
            'text': 'reply',
            'anchor': {'id': 'section.1'},
            'in_reply_to': note_id,
        })
        assert_equal(reply.status_code, 201)
        assert_equal(reply.data['in_reply_to'], note_id)

    def test_change(self):
        # create
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor': {'id': 'section.1'},
        })
        note_id = response.data['id']

        # change
        resp2 = self.client.patch('/api/documents/10/annotations/%s' % note_id, {
            'text': 'updated',
            'anchor': {'id': 'different'},
            'created_by_user': {'id': 99},
            'created_at': 'foo',
            'updated_at': 'bar',
        })
        assert_equal(resp2.status_code, 200)

        # verify
        resp3 = self.client.get('/api/documents/10/annotations/%s' % note_id)
        assert_equal(resp3.data['text'], 'updated')
        assert_equal(resp3.data['anchor'], {'id': 'different'})
        assert_equal(resp3.data['created_by_user'], response.data['created_by_user'])

    def test_cant_change_different_owner(self):
        # create
        response = self.client.post('/api/documents/10/annotations', {
            'text': 'hello',
            'anchor': {'id': 'section.1'},
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
            'anchor': {'id': 'section.1'},
        })
        note_id = response.data['id']

        # change user
        self.client.logout()

        # change
        response = self.client.patch('/api/documents/10/annotations/%s' % note_id, {
            'text': 'goodbye',
        })
        assert_equal(response.status_code, 403)
