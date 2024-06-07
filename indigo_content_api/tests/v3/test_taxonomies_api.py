from django.test import override_settings

from rest_framework.test import APITestCase


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TaxonomyTopicsAPIV3Test(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomy_topics', 'work', 'published', 'colophon',
                'attachments', 'commencements']
    api_path = '/api/v3'
    api_host = 'testserver'

    def setUp(self):
        self.client.login(username='api-user@example.com', password='password')

    def test_taxonomies(self):
        response = self.client.get(self.api_path + '/taxonomies.json')
        # /taxonomies isn't in v3
        self.assertEqual(404, response.status_code)

    def test_taxonomy_topics_list(self):
        response = self.client.get(self.api_path + '/taxonomy-topics.json')
        self.assertEqual(200, response.status_code)

        taxonomy_topic = response.json()['results'][0]
        self.assertEqual({
            'name': 'Laws.Africa Subject Areas',
            'slug': 'lawsafrica-subject-areas',
            'id': 1,
            'children': [{
                'name': 'Money and Business',
                'slug': 'lawsafrica-subject-areas-money-and-business',
                'id': 2,
                'children': []
            }, {
                'name': 'Children',
                'slug': 'lawsafrica-subject-areas-children',
                'id': 5,
                'children': []
            }, {
                'name': 'Communications',
                'slug': 'lawsafrica-subject-areas-communications',
                'id': 6,
                'children': []
            }, {
                'name': 'Estates, Trusts and Succession',
                'slug': 'lawsafrica-subject-areas-estates-trusts-and-succession',
                'id': 7,
                'children': []
            }]
        }, taxonomy_topic)

    def test_taxonomy_topic_root_detail(self):
        response = self.client.get(self.api_path + '/taxonomy-topics/lawsafrica-subject-areas.json')
        self.assertEqual(200, response.status_code)

        topic = response.json()
        self.assertEqual({
            'name': 'Laws.Africa Subject Areas',
            'slug': 'lawsafrica-subject-areas',
            'id': 1,
            'children': [{
                'name': 'Money and Business',
                'slug': 'lawsafrica-subject-areas-money-and-business',
                'id': 2,
                'children': []
            }, {
                'name': 'Children',
                'slug': 'lawsafrica-subject-areas-children',
                'id': 5,
                'children': []
            }, {
                'name': 'Communications',
                'slug': 'lawsafrica-subject-areas-communications',
                'id': 6,
                'children': []
            }, {
                'name': 'Estates, Trusts and Succession',
                'slug': 'lawsafrica-subject-areas-estates-trusts-and-succession',
                'id': 7,
                'children': []
            }]
        }, topic)

    def test_taxonomy_topic_child_detail(self):
        response = self.client.get(self.api_path + '/taxonomy-topics/lawsafrica-subject-areas-money-and-business.json')
        self.assertEqual(200, response.status_code)

        topic = response.json()
        self.assertEqual({
            "name": "Money and Business",
            "slug": "lawsafrica-subject-areas-money-and-business",
            "id": 2,
            "children": [],
        }, topic)

    def test_taxonomy_topic_work_expressions(self):
        response = self.client.get(self.api_path + '/taxonomy-topics/lawsafrica-subject-areas-money-and-business/work-expressions.json')
        self.assertEqual(200, response.status_code)

        frbr_uris = [r["frbr_uri"] for r in response.json()['results']]
        self.assertEqual(["/akn/za/act/2014/10", "/akn/za/act/1880/1"], frbr_uris)

    def test_taxonomy_topic_detail_not_public(self):
        self.assertEqual(404, self.client.get(self.api_path + '/taxonomy-topics/internal-topic.json').status_code)
        self.assertEqual(404, self.client.get(self.api_path + '/taxonomy-topics/internal-topic-im-private.json').status_code)

    def test_taxonomy_topic_work_expressions_not_public(self):
        self.assertEqual(404, self.client.get(self.api_path + '/taxonomy-topics/internal-topic/work-expressions.json').status_code)
        self.assertEqual(404, self.client.get(self.api_path + '/taxonomy-topics/internal-topic-im-private/work-expressions.json').status_code)
