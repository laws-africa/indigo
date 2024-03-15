from indigo_content_api.tests.v2.test_taxonomies_api import TaxonomiesAPIV2Test


class TaxonomyTopicsAPIV3Test(TaxonomiesAPIV2Test):
    fixtures = ['languages_data', 'taxonomies', 'taxonomy_topics', 'user']
    api_path = '/api/v3'

    def test_taxonomies(self):
        response = self.client.get(self.api_path + '/taxonomies.json')
        # /taxonomies isn't in v3
        self.assertEqual(404, response.status_code)

    def test_taxonomy_topics_list(self):
        response = self.client.get(self.api_path + '/taxonomy-topics.json')
        self.assertEqual(200, response.status_code)

        taxonomy_topics = response.json()['results']
        self.assertEqual([
            {
                "name": "Laws.Africa Subject Areas",
                "slug": "lawsafrica-subject-areas",
                "id": 1,
                "children": [
                    {
                        "name": "Money and Business",
                        "slug": "lawsafrica-subject-areas-money-and-business",
                        "id": 2,
                        "children": [],
                    },
                ],
            },
        ], taxonomy_topics)

    def test_taxonomy_topic_root_detail(self):
        response = self.client.get(self.api_path + '/taxonomy-topics/lawsafrica-subject-areas.json')
        self.assertEqual(200, response.status_code)

        topic = response.json()
        self.assertEqual({
            "name": "Laws.Africa Subject Areas",
            "slug": "lawsafrica-subject-areas",
            "id": 1,
            "children": [
                {
                    "name": "Money and Business",
                    "slug": "lawsafrica-subject-areas-money-and-business",
                    "id": 2,
                    "children": [],
                },
            ],
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

    def test_taxonomy_topic_detail_not_public(self):
        self.assertEqual(404, self.client.get(self.api_path + '/taxonomy-topics/internal-topic.json').status_code)
        self.assertEqual(404, self.client.get(self.api_path + '/taxonomy-topics/internal-topic-im-private.json').status_code)
