from nose.tools import *
from rest_framework.test import APITestCase

from indigo_api.tests.fixtures import *

class SimpleTest(APITestCase):
    fixtures = ['user']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')

    def test_simple_create(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2'
        })

        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za/act/1998/2')
        assert_equal(response.data['title'], '(untitled)')
        assert_equal(response.data['nature'], 'act')
        assert_equal(response.data['year'], '1998')
        assert_equal(response.data['number'], '2')

        # these should not be included directly, they should have URLs
        id = response.data['id']
        assert_not_in('content', response.data)
        assert_not_in('toc', response.data)
        assert_equal(response.data['content_url'], 'http://testserver/api/documents/%s/content' % id)
        assert_equal(response.data['toc_url'], 'http://testserver/api/documents/%s/toc' % id)

        response = self.client.get('/api/documents/%s/content' % response.data['id'])
        assert_equal(response.status_code, 200)

        assert_in('<p/>', response.data['content'])


    def test_create_with_locality(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za-cpt/act/1998/2',
            'draft': False,
        })

        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za-cpt/act/1998/2')

        response = self.client.get('/api/za-cpt/act/1998/2')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['frbr_uri'], '/za-cpt/act/1998/2')

    def test_update_content(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'content': document_fixture('in the body')})
        assert_equal(response.status_code, 200)

        response = self.client.get('/api/documents/%s/content' % id)
        assert_equal(response.status_code, 200)
        assert_in('<p>in the body</p>', response.data['content'])

        # also try updating the content at /content
        response = self.client.put('/api/documents/%s/content' % id, {'content': document_fixture('also in the body')})
        assert_equal(response.status_code, 200)

        response = self.client.get('/api/documents/%s/content' % id)
        assert_equal(response.status_code, 200)
        assert_in('<p>also in the body</p>', response.data['content'])

    def test_create_with_content(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'content': document_fixture('in the body'),
            })
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.get('/api/documents/%s/content' % id)
        assert_equal(response.status_code, 200)
        assert_in('<p>in the body</p>', response.data['content'])

    def test_create_with_bad_content(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'content': 'not valid xml',
            })
        assert_equal(response.status_code, 400)
        assert_equal(len(response.data['content']), 1)

    def test_create_with_bad_uri(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/',
            'content': document_fixture('in the body'),
            })
        assert_equal(response.status_code, 400)
        assert_equal(len(response.data['frbr_uri']), 1)

    def test_table_of_contents(self):
        xml = """
          <chapter id="chapter-2">
            <num>2</num>
            <heading>Administrative provisions</heading>
            <section id="section-3">
              <num>3.</num>
              <heading>Consent required for <term refersTo="#term-interment" id="trm80">interment</term></heading>
              <subsection id="section-3.1">
                <num>(1)</num>
                <content><p>hello</p></content>
              </subsection>
            </section>
          </chapter>
        """

        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'content': document_fixture(xml=xml),
            })
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.get('/api/documents/%s/toc' % id)
        assert_equal(response.status_code, 200)

        self.maxDiff = None
        self.assertEqual(response.data['toc'], [
            {
                'type': 'chapter',
                'num': '2',
                'heading': 'Administrative provisions',
                'id': 'chapter-2',
                'component': 'main',
                'subcomponent': 'chapter/2',
                'url': 'http://testserver/api/za/act/1900/1/eng/main/chapter/2',
                'children': [
                    {
                        'type': 'section',
                        'num': '3.',
                        'heading': 'Consent required for interment',
                        'id': 'section-3',
                        'component': 'main',
                        'subcomponent': 'section/3',
                        'url': 'http://testserver/api/za/act/1900/1/eng/main/section/3',
                    },
                ],
            },
            ])
