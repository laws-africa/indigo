from nose.tools import *
from rest_framework.test import APITestCase

def body_fixture(text):
    return '<body><section id="section-1"><content><p>%s</p></content></section></body>' % text


class SimpleTest(APITestCase):
    fixtures = ['user']

    def test_simple_create(self):
        self.client.login(username='email@example.com', password='password')

        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2/'
        })

        self.assertEqual(response.status_code, 201)
        assert_equal(response.data['frbr_uri'], '/za/act/1998/2/')
        assert_equal(response.data['title'], '(untitled)')
        assert_equal(response.data['nature'], 'act')
        assert_equal(response.data['year'], '1998')
        assert_equal(response.data['number'], '2')

        response = self.client.get('/api/documents/%s/body' % response.data['id'])
        self.assertEqual(response.status_code, 200)

        assert_equal(response.data['body'], '<body xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n  <section id="section-1">\n    <content>\n      <p/>\n    </content>\n  </section>\n</body>\n')

    def test_update_body(self):
        self.client.login(username='email@example.com', password='password')

        response = self.client.post('/api/documents', {'frbr_uri': '/za/act/1998/2/'})
        self.assertEqual(response.status_code, 201)
        id = response.data['id']

        response = self.client.patch('/api/documents/%s' % id, {'body': body_fixture('in the body')})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/documents/%s/body' % id)
        self.assertEqual(response.status_code, 200)
        assert_in('<p>in the body</p>', response.data['body'])

        # also try updating the body at /body
        response = self.client.put('/api/documents/%s/body' % id, {'body': body_fixture('also in the body')})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/documents/%s/body' % id)
        self.assertEqual(response.status_code, 200)
        assert_in('<p>also in the body</p>', response.data['body'])

    def test_create_with_body(self):
        self.client.login(username='email@example.com', password='password')

        response = self.client.post('/api/documents', {
            'frbr_uri': '/za/act/1998/2/',
            'body': body_fixture('in the body'),
            })
        self.assertEqual(response.status_code, 201)
        id = response.data['id']

        response = self.client.get('/api/documents/%s/body' % id)
        self.assertEqual(response.status_code, 200)
        assert_in('<p>in the body</p>', response.data['body'])
