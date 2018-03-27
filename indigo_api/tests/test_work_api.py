# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from django.test.utils import override_settings

from indigo_api.tests.fixtures import *  # noqa


# Disable pipeline storage - see https://github.com/cyberdelia/django-pipeline/issues/277
@override_settings(STATICFILES_STORAGE='pipeline.storage.PipelineStorage', PIPELINE_ENABLED=False)
class WorkAPITest(APITestCase):
    fixtures = ['user', 'work', 'drafts']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')

    def test_delete_cascades(self):
        response = self.client.get('/api/documents/20')
        assert_equal(response.status_code, 200)

        response = self.client.delete('/api/works/7')
        assert_equal(response.status_code, 204)

        # should be gone
        response = self.client.get('/api/documents/20')
        assert_equal(response.status_code, 404)

    def test_validates_uri(self):
        response = self.client.post('/api/works', {
            'frbr_uri': 'bad'
        })
        assert_equal(response.status_code, 400)

        response = self.client.post('/api/works', {
            'frbr_uri': ''
        })
        assert_equal(response.status_code, 400)
