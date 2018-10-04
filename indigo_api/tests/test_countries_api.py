from rest_framework.test import APITestCase


class CountriesAPITest(APITestCase):
    fixtures = ['countries', 'user', 'editor']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')

    def test_basic_api(self):
        response = self.client.get('/api/countries')
        self.assertEqual(response.status_code, 200)

        za = next(c for c in response.data['results'] if c['code'] == 'za')
        self.assertEqual(za['name'], 'South Africa')
