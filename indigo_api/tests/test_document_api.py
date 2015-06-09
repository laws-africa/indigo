from nose.tools import *  # noqa
from rest_framework.test import APITestCase

from indigo_api.tests.fixtures import *  # noqa


class DocumentAPITest(APITestCase):
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
        assert_equal(response.data['amendments'], [])
        assert_equal(response.data['amended_versions'], [])

        # these should not be included directly, they should have URLs
        id = response.data['id']
        assert_not_in('content', response.data)
        assert_not_in('toc', response.data)
        assert_equal(response.data['content_url'], 'http://testserver/api/documents/%s/content' % id)
        assert_equal(response.data['toc_url'], 'http://testserver/api/documents/%s/toc' % id)

        response = self.client.get('/api/documents/%s/content' % response.data['id'])
        assert_equal(response.status_code, 200)

        assert_in('<p/>', response.data['content'])

    def test_create_with_tags(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'tags': ['foo', 'bar']
        })

        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za/act/1998/2')
        assert_equal(sorted(response.data['tags']), ['bar', 'foo'])

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

    def test_create_title_overrides_content_xml(self):
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za-cpt/act/1998/2',
            'content': document_fixture('in the body'),
            'title': 'Document title',
            'draft': True,
            'tags': ['a'],
        })
        id = response.data['id']

        assert_equal(response.status_code, 201)
        assert_equal(response.data['title'], 'Document title')

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['title'], 'Document title')

    def test_update(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'tags': ['foo', 'bar']})
        assert_equal(response.status_code, 200)
        # TODO: this should work
        #assert_equal(sorted(response.data['tags']), ['bar', 'foo'])

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(sorted(response.data['tags']), ['bar', 'foo'])

    def test_update_publication_date(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'publication_date': '2015-01-01'})
        assert_equal(response.status_code, 200)
        assert_equal(response.data['publication_date'], '2015-01-01')

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['publication_date'], '2015-01-01')

    def test_update_expression_date(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'expression_date': '2015-01-01'})
        assert_equal(response.status_code, 200)
        assert_equal(response.data['expression_date'], '2015-01-01')

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['expression_date'], '2015-01-01')

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

    def test_frbr_uri_lowercased(self):
        # ACT should be changed to act
        response = self.client.post('/api/documents', {'frbr_uri': '/za/ACT/1998/2'})
        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za/act/1998/2')

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

    def test_delete(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.delete('/api/documents/%s' % id)
        assert_equal(response.status_code, 204)

    def test_cannot_delete(self):
        # this user cannot delete
        self.client.login(username='non-deleter@example.com', password='password')

        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.delete('/api/documents/%s' % id)
        assert_equal(response.status_code, 403)

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
                'url': 'http://testserver/api/za/act/1998/2/eng/main/chapter/2',
                'children': [
                    {
                        'type': 'section',
                        'num': '3.',
                        'heading': 'Consent required for interment',
                        'id': 'section-3',
                        'component': 'main',
                        'subcomponent': 'section/3',
                        'url': 'http://testserver/api/za/act/1998/2/eng/main/section/3',
                    },
                ],
            },
            ])

    def test_create_with_amendments(self):
        # this document made the amendments
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/2010/2',
            'expression_date': '2010-01-01',
        })
        assert_equal(response.status_code, 201)
        amending_id = response.data['id']
        assert_is_not_none(amending_id)

        # this is the amended document
        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2',
            'amendments': [{
                'date': '2010-01-01',
                'amending_title': 'Act 2 of 2010',
                'amending_uri': '/za/act/2010/2',
            }]
        })
        assert_equal(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za/act/1998/2')
        assert_equal(response.data['amendments'], [{
            'date': '2010-01-01',
            'amending_title': 'Act 2 of 2010',
            'amending_uri': '/za/act/2010/2',
            'amending_id': amending_id,
        }])

        # ensure it shows amending_id when listed
        response = self.client.get('/api/documents')
        assert_equal(response.status_code, 200)
        doc = list(d for d in response.data if d['frbr_uri'] == '/za/act/1998/2')[0]
        assert_equal(doc['amendments'], [{
            'date': '2010-01-01',
            'amending_title': 'Act 2 of 2010',
            'amending_uri': '/za/act/2010/2',
            'amending_id': amending_id,
        }])

    def test_update_with_amendments(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {
            'amendments': [{
                'date': '2010-01-01',
                'amending_title': 'Act 2 of 2010',
                'amending_uri': '/za/act/2010/2',
            }]
        })

        assert_equal(response.status_code, 200)
        assert_equal(response.data['amendments'], [{
            'date': '2010-01-01',
            'amending_title': 'Act 2 of 2010',
            'amending_uri': '/za/act/2010/2',
            'amending_id': None,
        }])

    def test_update_with_repeal(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {
            'repeal': {
                'date': '2010-01-01',
                'repealing_title': 'Act 2 of 2010',
                'repealing_uri': '/za/act/2010/2',
            }
        })

        assert_equal(response.status_code, 200)
        assert_equal(response.data['repeal'], {
            'date': '2010-01-01',
            'repealing_title': 'Act 2 of 2010',
            'repealing_uri': '/za/act/2010/2',
            'repealing_id': None,
        })

        response = self.client.get('/api/documents/%s' % id)
        assert_equal(response.status_code, 200)
        assert_equal(response.data['repeal'], {
            'date': '2010-01-01',
            'repealing_title': 'Act 2 of 2010',
            'repealing_uri': '/za/act/2010/2',
            'repealing_id': None,
        })

    def test_update_null_repeal(self):
        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2'})
        assert_equal(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {
            'repeal': None,
        })

        assert_equal(response.status_code, 200)
        assert_equal(response.data['repeal'], None)
