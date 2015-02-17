from nose.tools import *
from rest_framework.test import APITestCase

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
