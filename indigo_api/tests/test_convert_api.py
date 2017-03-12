# -*- coding: utf-8 -*-

import tempfile
from datetime import date
import os.path
import re

from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer

from indigo_api.tests.fixtures import *  # noqa


class RenderParseAPITest(APITestCase):
    fixtures = ['user', 'published']

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
            },
        }, format='json')
        assert_equal(response.status_code, 200)

    def test_render_with_empty_publication(self):
        response = self.client.post('/api/render', {
            'document': {
                'content': document_fixture(text='hello'),
                'publication_name': '',
                'publication_number': '',
            },
        }, format='json')
        assert_equal(response.status_code, 200)

    def test_render_json_to_html(self):
        response = self.client.post('/api/render', {
            'document': {
                'frbr_uri': '/za/act/1980/20',
                'content': document_fixture(text='hello'),
            },
        })
        assert_equal(response.status_code, 200)
        assert_true(response.data['output'].startswith('\n\n<div'))
        assert_in('Act 20 of 1980', response.data['output'])

    def test_render_json_to_html_round_trip(self):
        response = self.client.get('/api/za/act/2001/8/eng.json')

        data = response.data
        data['content'] = document_fixture(text='hello')

        response = self.client.post('/api/render', {
            'document': data,
        })
        assert_equal(response.status_code, 200)
        assert_true(response.data['output'].startswith('\n\n<div'))
        assert_in('Repealed Act', response.data['output'])

    def test_render_json_to_html_with_unicode(self):
        response = self.client.post('/api/render', {
            'document': {
                'frbr_uri': '/za/act/1980/20',
                'content': document_fixture(text=u'hello κόσμε'),
            },
        })
        assert_equal(response.status_code, 200)
        assert_true(response.data['output'].startswith('\n\n<div'))
        assert_in('Act 20 of 1980', response.data['output'])

    def test_parse_text_fragment(self):
        response = self.client.post('/api/parse', {
            'content': """
                Chapter 2
                The Beginning
                1. First Verse
                κόσμε
                (1) In the beginning
                (2) There was nothing
            """,
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
          <p>There was nothing</p>
        </content>
      </subsection>
    </section>
  </chapter>
</akomaNtoso>
""", response.data['output'].decode('utf-8'))

    def test_parse_file(self):
        tmp_file = tempfile.NamedTemporaryFile(suffix='.txt')
        tmp_file.write("""
        Chapter 2
        The Beginning
        1. First Verse
        κόσμε
        (1) In the beginning
        (2) There was nothing
        """)
        tmp_file.seek(0)
        fname = os.path.basename(tmp_file.name)

        response = self.client.post('/api/parse', {
            'file': tmp_file,
        }, format='multipart')
        assert_equal(response.status_code, 200)

        today = date.today().strftime('%Y-%m-%d')
        output = response.data['output'].decode('utf-8')
        frbr_uri = re.search(r'<FRBRuri value="(.*?)"/>', output).groups(0)[0]

        self.maxDiff = None
        self.assertEqual(output, u"""<akomaNtoso xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.akomantoso.org/2.0" xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd">
  <act contains="originalVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value=\"""" + frbr_uri + u"""/main"/>
          <FRBRuri value=\"""" + frbr_uri + u""""/>
          <FRBRalias value="Imported from """ + fname + u""""/>
          <FRBRdate date="" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value=\"""" + frbr_uri + u"""/eng@1980-01-01/main"/>
          <FRBRuri value=\"""" + frbr_uri + u"""/eng@1980-01-01"/>
          <FRBRdate date="1980-01-01" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value=\"""" + frbr_uri + u"""/eng@1980-01-01/main"/>
          <FRBRuri value=\"""" + frbr_uri + u"""/eng@1980-01-01"/>
          <FRBRdate date=\"""" + today + u"""\" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <references source="#this">
        <TLCOrganization id="slaw" href="https://github.com/longhotsummer/slaw" showAs="Slaw"/>
        <TLCOrganization id="council" href="/ontology/organization/za/council" showAs="Council"/>
      </references>
    </meta>
    <body>
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
              <p>There was nothing</p>
            </content>
          </subsection>
        </section>
      </chapter>
    </body>
  </act>
</akomaNtoso>
""")
