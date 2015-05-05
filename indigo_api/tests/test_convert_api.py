# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase

from indigo_api.tests.fixtures import *  # noqa


class ConvertAPITest(APITestCase):
    fixtures = ['user']

    def setUp(self):
        self.client.default_format = 'json'
        self.client.login(username='email@example.com', password='password')

    def test_convert_no_output(self):
        response = self.client.post('/api/convert', {
            'content': {
                'frbr_uri': '/',
                'content': document_fixture(text='hello'),
            },
            'inputformat': 'application/json',
            })
        assert_equal(response.status_code, 400)
        assert_in('outputformat', response.data)

    def test_convert_no_inputformat(self):
        response = self.client.post('/api/convert', {
            'content': {
                'frbr_uri': '/',
                'content': document_fixture(text='hello'),
            },
            'outputformat': 'application/json',
            })
        assert_equal(response.status_code, 400)
        assert_in('inputformat', response.data)


    def test_convert_json(self):
        response = self.client.post('/api/convert', {
            'content': {
                'content': document_fixture(text='hello'),
                # these should be ignored
                'tags': ['foo', 'bar'],
            },
            'inputformat': 'application/json',
            'outputformat': 'application/json',
            })
        assert_equal(response.status_code, 200)
        assert_equal(response.data['frbr_uri'], '/za/act/1900/1')
        assert_true(response.data['content'].startswith('<akomaNtoso'))
        assert_is_none(response.data['tags'])
        assert_is_none(response.data['id'])

    def test_convert_json_to_xml(self):
        response = self.client.post('/api/convert', {
            'content': {
                'frbr_uri': '/za/act/1980/02',
                'content': document_fixture(text='hello'),
            },
            'inputformat': 'application/json',
            'outputformat': 'application/xml',
            })
        assert_equal(response.status_code, 200)
        assert_true(response.data['output'].startswith('<akomaNtoso'))
        assert_in('hello', response.data['output'])

    def test_convert_json_to_html(self):
        response = self.client.post('/api/convert', {
            'content': {
                'frbr_uri': '/za/act/1980/20',
                'content': document_fixture(text='hello'),
            },
            'inputformat': 'application/json',
            'outputformat': 'text/html',
            })
        assert_equal(response.status_code, 200)
        assert_true(response.data['output'].startswith('<div'))
        assert_in('Act 20 of 1980', response.data['output'])

    def test_convert_json_to_html_with_unicode(self):
        response = self.client.post('/api/convert', {
            'content': {
                'frbr_uri': '/za/act/1980/20',
                'content': document_fixture(text='hello κόσμε'),
            },
            'inputformat': 'application/json',
            'outputformat': 'text/html',
            })
        assert_equal(response.status_code, 200)
        assert_true(response.data['output'].startswith('<div'))
        assert_in('Act 20 of 1980', response.data['output'])

    def test_convert_text_fragment(self):
        response = self.client.post('/api/convert', {
            'content': """
                Chapter 2
                The Beginning
                1. First Verse
                κόσμε
                (1) In the beginning
                (2) There was nothing
            """,
            'inputformat': 'text/plain',
            'outputformat': 'application/xml',
            'fragment': 'chapter',
            'id_prefix': 'prefix',
            })
        assert_equal(response.status_code, 200)
        self.maxDiff = None
        self.assertEqual(u"""<akomaNtoso xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.akomantoso.org/2.0" xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd">
  <chapter id="chapter-2">
    <num>2</num>
    <heading>The Beginning</heading>
    <section id="section-1">
      <num>1.</num>
      <heading>First Verse</heading>
      <subsection id="section-1.subsection-0">
        <content>
          <p>κόσμε</p>
        </content>
      </subsection>
      <subsection id="section-1.1">
        <num>(1)</num>
        <content>
          <p>In the beginning</p>
        </content>
      </subsection>
      <subsection id="section-1.2">
        <num>(2)</num>
        <content>
          <p>There was nothing</p>
        </content>
      </subsection>
    </section>
  </chapter>
</akomaNtoso>
""", response.data['output'].decode('utf-8'))
