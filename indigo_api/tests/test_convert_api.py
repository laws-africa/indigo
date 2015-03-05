from nose.tools import *
from rest_framework.test import APITestCase

from indigo_api.tests.fixtures import *

class ConvertAPITest(APITestCase):
    fixtures = ['user']

    def setUp(self):
        self.client.default_format = 'json'
        self.client.login(username='email@example.com', password='password')

    def test_convert_no_output(self):
        response = self.client.post('/api/convert', {
            'content': {
                'frbr_uri': '/',
                'body': body_fixture('hello'),
            },
            'inputformat': 'json',
            })
        assert_equal(response.status_code, 400)
        assert_in('outputformat', response.data)

    def test_convert_no_inputformat(self):
        response = self.client.post('/api/convert', {
            'content': {
                'frbr_uri': '/',
                'body': body_fixture('hello'),
            },
            'outputformat': 'json',
            })
        assert_equal(response.status_code, 400)
        assert_in('inputformat', response.data)


    def test_convert_json(self):
        response = self.client.post('/api/convert', {
            'content': {
                'body': body_fixture('hello'),
            },
            'inputformat': 'json',
            'outputformat': 'json',
            })
        assert_equal(response.status_code, 200)
        assert_equal(response.data['frbr_uri'], '/')
        assert_true(response.data['content'].startswith('<akomaNtoso'))
        assert_is_none(response.data['id'])

    def test_convert_json_to_xml(self):
        response = self.client.post('/api/convert', {
            'content': {
                'frbr_uri': '/',
                'body': body_fixture('hello'),
            },
            'inputformat': 'json',
            'outputformat': 'xml',
            })
        assert_equal(response.status_code, 200)
        assert_true(response.data.startswith('<akomaNtoso'))
        assert_in('hello', response.data)

    def test_convert_json_to_html(self):
        response = self.client.post('/api/convert', {
            'content': {
                'frbr_uri': '/',
                'body': body_fixture('hello'),
            },
            'inputformat': 'json',
            'outputformat': 'html',
            })
        assert_equal(response.status_code, 200)
        assert_true(response.data.startswith('<span'))
        assert_in('hello', response.data)

