from nose.tools import *  # noqa
from rest_framework.test import APITestCase


class CountriesAPITest(APITestCase):
    fixtures = ['countries', 'user']

    def setUp(self):
        self.client.login(username='api-user@example.com', password='password')

    def test_countries(self):
        response = self.client.get('/api/v1/countries')
        assert_equal(response.status_code, 200)
        assert_equal(response.data['count'], 2)
