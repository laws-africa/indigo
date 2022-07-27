# -*- coding: utf-8 -*-

from nose.tools import assert_equal, assert_not_equal
from rest_framework.test import APITestCase
from django.test.utils import override_settings

from indigo_api.models import Work


# Disable pipeline storage - see https://github.com/cyberdelia/django-pipeline/issues/277
@override_settings(STATICFILES_STORAGE='pipeline.storage.PipelineStorage', PIPELINE_ENABLED=False)
class WorkAPITest(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'work', 'drafts', 'published']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')

    def test_prevent_delete(self):
        work = Work.objects.get(pk=7)

        self.assertRedirects(self.client.post('/works%s/delete' % work.frbr_uri), '/works%s/edit/' % work.frbr_uri)

        # delete linked documents
        work.expressions().delete()

        # now can delete
        self.assertRedirects(self.client.post('/works%s/delete' % work.frbr_uri), '/places/za/')

    def test_filters(self):
        response = self.client.get('/api/works?country=za')
        assert_equal(response.status_code, 200)
        assert_equal(response.data['results'], [])

        response = self.client.get('/api/works?country=xy')
        assert_equal(response.status_code, 200)
        assert_equal(response.data['results'], [])
