from indigo_content_api.tests.v2.test_taxonomies_api import TaxonomiesAPIV2Test


class TaxonomyTopicsAPIV3Test(TaxonomiesAPIV2Test):
    fixtures = ['languages_data', 'taxonomies', 'taxonomy_topics', 'user']
    api_path = '/api/v3'

    def test_taxonomies(self):
        response = self.client.get(self.api_path + '/taxonomies.json')
        # /taxonomies isn't in v3
        self.assertEqual(404, response.status_code)

        response = self.client.get(self.api_path + '/taxonomy_topics.json')
        self.assertEqual(200, response.status_code)

        taxonomy_topics = response.json()['results']
        self.assertEqual([
            {
                "name": "Projects",
                "slug": "projects",
                "children": [
                    {
                        "name": "Priority: High",
                        "slug": "projects-priority-high",
                        "children": [],
                    },
                    {
                        "name": "Priority: Medium",
                        "slug": "projects-priority-medium",
                        "children": [],
                    },
                    {
                        "name": "Priority: Low",
                        "slug": "projects-priority-low",
                        "children": [
                            {
                                "name": "A workflow",
                                "slug": "projects-priority-low-a-workflow",
                                "children": [],
                            },
                        ],
                    },
                ],
            },
            {
                "name": "Laws.Africa Subject Areas",
                "slug": "lawsafrica-subject-areas",
                "children": [
                    {
                        "name": "Money and Business",
                        "slug": "lawsafrica-subject-areas-money-and-business",
                        "children": [],
                    },
                ],
            },
        ], taxonomy_topics)
