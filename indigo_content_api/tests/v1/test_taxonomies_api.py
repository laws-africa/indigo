from rest_framework.test import APITestCase
import json


class TaxonomiesAPIV1Test(APITestCase):
    fixtures = ['languages_data', 'taxonomies', 'user']
    api_path = '/api/v1'
    api_host = 'testserver'

    def setUp(self):
        self.client.login(username='api-user@example.com', password='password')

    def test_taxonomies(self):
        response = self.client.get(self.api_path + '/taxonomies.json')
        self.assertEqual(response.status_code, 200)

        # sort them so we can compare them easily
        taxonomies = sorted(json.loads(json.dumps(response.data['results'])), key=lambda t: t['vocabulary'])
        for tax in taxonomies:
            tax['topics'].sort(key=lambda t: (t['level_1'], t['level_2']))

        self.assertEqual([{
            "vocabulary": "",
            "title": "Third Party Taxonomy",
            "topics": [
                {
                    "level_1": "Fun stuff",
                    "level_2": None,
                },
                {
                    "level_1": "Not so fun stuff",
                    "level_2": None,
                },
            ],
        }, {
            "vocabulary": "lawsafrica-subjects",
            "title": "Laws.Africa Subject Taxonomy",
            "topics": [
                {
                    "level_1": "Money and Business",
                    "level_2": "Banking"
                },
                {
                    "level_1": "Money and Business",
                    "level_2": "Finance"
                },
                {
                    "level_1": "People and Work",
                    "level_2": "Children"
                },
                {
                    "level_1": "People and Work",
                    "level_2": "Communications"
                },
            ],
        }], taxonomies)
