from rest_framework.test import APITestCase


class PlacesAPIV3Test(APITestCase):
    fixtures = ['languages_data', 'countries', 'user']
    api_path = '/api/v3'
    api_host = 'testserver'

    def setUp(self):
        self.client.login(username='api-user@example.com', password='password')

    def test_places(self):
        response = self.client.get(self.api_path + '/places')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

    def test_country(self):
        response = self.client.get(self.api_path + '/places/za')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], "za")
        self.assertEqual(response.data['frbr_uri_code'], "za")
        self.assertIn("localities", response.data)

    def test_locality(self):
        response = self.client.get(self.api_path + '/places/za-cpt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], "cpt")
        self.assertEqual(response.data['frbr_uri_code'], "za-cpt")
        self.assertNotIn("localities", response.data)
