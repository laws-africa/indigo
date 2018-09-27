# -*- coding: utf-8 -*-

from nose.tools import assert_equal, assert_not_equal
from rest_framework.test import APITestCase
from django.test.utils import override_settings

from indigo_api.models import Work


# Disable pipeline storage - see https://github.com/cyberdelia/django-pipeline/issues/277
@override_settings(STATICFILES_STORAGE='pipeline.storage.PipelineStorage', PIPELINE_ENABLED=False)
class WorkAPITest(APITestCase):
    fixtures = ['countries', 'user', 'editor', 'work', 'drafts', 'published']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')

    def test_prevent_delete(self):
        response = self.client.get('/api/documents/20')
        assert_equal(response.status_code, 200)

        response = self.client.delete('/api/works/7')
        assert_equal(response.status_code, 405)

        # delete document
        response = self.client.delete('/api/documents/20')
        assert_equal(response.status_code, 204)

        # now can delete
        response = self.client.delete('/api/works/7')
        assert_equal(response.status_code, 204)

    def test_cascade_frbr_uri_changes(self):
        response = self.client.get('/api/documents/20')
        assert_equal(response.status_code, 200)
        assert_equal(response.data['frbr_uri'], '/za/act/1945/1')

        response = self.client.patch('/api/works/7', {'frbr_uri': '/za/act/2999/1'})
        assert_equal(response.status_code, 200)

        response = self.client.get('/api/documents/20')
        assert_equal(response.status_code, 200)
        assert_equal(response.data['frbr_uri'], '/za/act/2999/1')

    def test_validates_uri(self):
        response = self.client.post('/api/works', {
            'frbr_uri': 'bad'
        })
        assert_equal(response.status_code, 400)

        response = self.client.post('/api/works', {
            'frbr_uri': ''
        })
        assert_equal(response.status_code, 400)

    def test_update_publication_date(self):
        response = self.client.post('/api/works', {'frbr_uri': '/za/act/2005/2', 'title': 'test', 'language': 'eng', 'country': 'za'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/works/%s' % id, {'publication_date': '2015-01-01'})
        assert_equal(response.status_code, 200)
        assert_equal(response.data['publication_date'], '2015-01-01')

        response = self.client.get('/api/works/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['publication_date'], '2015-01-01')

    def test_update_with_repeal(self):
        response = self.client.patch('/api/works/1', {
            'repealed_by': 2,
            'repealed_date': '2010-01-01',
        })
        assert_equal(response.status_code, 200)

        response = self.client.get('/api/documents/1')
        assert_equal(response.status_code, 200)
        assert_equal(response.data['repeal'], {
            'date': '2010-01-01',
            'repealing_title': 'Test Act',
            'repealing_uri': '/za/act/1998/2',
        })

    def test_update_null_repeal(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2', 'expression_date': '2001-01-01', 'language': 'eng'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {
            'repeal': None,
        })

        assert_equal(response.status_code, 200)
        assert_equal(response.data['repeal'], None)

    def test_filters(self):
        response = self.client.get('/api/works?country=za')
        assert_equal(response.status_code, 200)
        assert_not_equal(len(response.data['results']), 0)

        response = self.client.get('/api/works?country=xx')
        assert_equal(response.status_code, 200)
        assert_equal(len(response.data['results']), 0)

    def test_publication_date_updates_documents(self):
        work = Work.objects.get(frbr_uri='/za/act/1945/1')
        initial = work.initial_expressions()
        assert_equal(initial[0].publication_date.strftime('%Y-%m-%d'), "1945-10-12")

        response = self.client.patch('/api/works/%s' % work.id, {'publication_date': '1945-12-12'})
        assert_equal(response.status_code, 200)

        work = Work.objects.get(frbr_uri='/za/act/1945/1')
        initial = list(work.initial_expressions().all())
        assert_equal(initial[0].publication_date.strftime('%Y-%m-%d'), "1945-12-12")
        assert_equal(len(initial), 1)
