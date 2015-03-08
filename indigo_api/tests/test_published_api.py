from nose.tools import *
from rest_framework import status
from rest_framework.test import APITestCase

class PublishedAPITest(APITestCase):
    fixtures = ['user', 'published']

    def test_published_json(self):
        response = self.client.get('/api/za/act/2014/10')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['frbr_uri'], '/za/act/2014/10')

        response = self.client.get('/api/za/act/2014/10.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['frbr_uri'], '/za/act/2014/10')

        response = self.client.get('/api/za/act/2014/10/eng.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['frbr_uri'], '/za/act/2014/10')

    def test_published_xml(self):
        response = self.client.get('/api/za/act/2014/10.xml')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/xml')
        assert_in('<akomaNtoso', response.content)

        response = self.client.get('/api/za/act/2014/10/eng.xml')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/xml')
        assert_in('<akomaNtoso', response.content)

    def test_published_html(self):
        response = self.client.get('/api/za/act/2014/10.html')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'text/html')
        assert_not_in('<akomaNtoso', response.content)
        assert_in('<div', response.content)

        response = self.client.get('/api/za/act/2014/10/eng.html')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'text/html')
        assert_not_in('<akomaNtoso', response.content)
        assert_in('<div', response.content)

    def test_published_listing(self):
        response = self.client.get('/api/za/')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(len(response.data), 1)

        response = self.client.get('/api/za/act/')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(len(response.data), 1)

        response = self.client.get('/api/za/act/2014')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(len(response.data), 1)

    def test_published_missing(self):
        assert_equal(self.client.get('/api/za/act/2999/22').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22.html').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22.xml').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22.json').status_code, 404)

        assert_equal(self.client.get('/api/za/act/2999/22/eng').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22/eng.html').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22/eng.xml').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22/eng.json').status_code, 404)

    def test_published_wrong_language(self):
        assert_equal(self.client.get('/api/za/act/2014/10/fre').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2014/10/fre.html').status_code, 404)

    def test_published_listing_missing(self):
        assert_equal(self.client.get('/api/za/act/2999/').status_code, 404)
        assert_equal(self.client.get('/api/zm/').status_code, 404)

    def test_published_toc(self):
        response = self.client.get('/api/za/act/2014/10/eng/toc.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['toc'], [{'id': 'section-1', 'type': 'section'}])
