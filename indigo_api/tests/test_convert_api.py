# -*- coding: utf-8 -*-

import tempfile
from datetime import date

from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer

from indigo_api.tests.fixtures import *  # noqa


class RenderParseAPITest(APITestCase):
    fixtures = ['countries', 'user', 'editor', 'work', 'published']

    def setUp(self):
        self.client.default_format = 'json'
        JSONRenderer.charset = 'utf-8'
        self.client.login(username='email@example.com', password='password')

    def test_render_with_null_publication(self):
        response = self.client.post('/api/render', {
            'document': {
                'content': document_fixture(text='hello'),
                'publication_name': None,
                'publication_number': None,
                'publication_date': None,
                'expression_date': '2001-01-01',
                'language': 'eng',
            },
        }, format='json')
        assert_equal(response.status_code, 200)

    def test_render_with_empty_publication(self):
        response = self.client.post('/api/render', {
            'document': {
                'content': document_fixture(text='hello'),
                'publication_name': '',
                'publication_number': '',
                'expression_date': '2001-01-01',
                'language': 'eng',
            },
        }, format='json')
        assert_equal(response.status_code, 200)

    def test_render_json_to_html(self):
        response = self.client.post('/api/render', {
            'document': {
                'frbr_uri': '/za/act/1998/2',
                'content': document_fixture(text='hello'),
                'expression_date': '2001-01-01',
                'language': 'eng',
            },
        })
        assert_equal(response.status_code, 200)
        assert_in('<div class="coverpage">', response.data['output'])
        assert_in('Act 2 of 1998', response.data['output'])

    def test_render_json_to_html_round_trip(self):
        response = self.client.get('/api/documents/4.json')
        assert_equal(response.status_code, 200)

        data = response.data
        data['content'] = document_fixture(text='hello')

        response = self.client.post('/api/render', {
            'document': data,
        })
        assert_equal(response.status_code, 200)
        assert_in('<div class="coverpage">', response.data['output'])
        assert_in('Repealed Act', response.data['output'])

    def test_render_json_to_html_with_unicode(self):
        response = self.client.post('/api/render', {
            'document': {
                'frbr_uri': '/za/act/1998/2',
                'content': document_fixture(text=u'hello κόσμε'),
                'expression_date': '2001-01-01',
                'language': 'eng',
            },
        })
        assert_equal(response.status_code, 200)
        assert_in('<div class="coverpage">', response.data['output'])
        assert_in('Act 2 of 1998', response.data['output'])

    def test_parse_text_fragment(self):
        response = self.client.post('/api/parse', {
            'content': """
                Chapter 2
                The Beginning
                1. First Verse
                κόσμε
                (1) In the beginning
                (2) There was nothing and an Act no 2 of 2010.
            """,
            'fragment': 'chapter',
            'id_prefix': 'prefix',
            'frbr_uri': '/za/act/1998/2',
            'language': 'eng',
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
      <paragraph id="section-1.paragraph-0">
        <content>
          <p>κόσμε</p>
        </content>
      </paragraph>
      <subsection id="section-1.1">
        <num>(1)</num>
        <content>
          <p>In the beginning</p>
        </content>
      </subsection>
      <subsection id="section-1.2">
        <num>(2)</num>
        <content>
          <p>There was nothing and an Act no 2 of 2010.</p>
        </content>
      </subsection>
    </section>
  </chapter>
</akomaNtoso>
""", response.data['output'].decode('utf-8'))
