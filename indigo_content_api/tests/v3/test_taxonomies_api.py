from indigo_content_api.tests.v2.test_taxonomies_api import TaxonomiesAPIV2Test


class TaxonomyTopicsAPIV3Test(TaxonomiesAPIV2Test):
    api_path = '/api/v3'

    def test_taxonomies(self):
        response = self.client.get(self.api_path + '/taxonomies.json')
        self.assertEqual(404, response.status_code)

        response = self.client.get(self.api_path + '/taxonomy_topics.json')
        self.assertEqual(200, response.status_code)

        self.assertEqual([
            {
                "name": "Third Party Taxonomy",
                "slug": "third-party-taxonomy",
                "children": [
                    {
                        "name": "Fun stuff",
                        "slug": "third-party-taxonomy-fun-stuff",
                        "children": [],
                    },
                    {
                        "name": "Not so fun stuff",
                        "slug": "third-party-taxonomy-not-so-fun-stuff",
                        "children": [],
                    },
                ],
            }, {
                "name": "Laws.Africa Subject Taxonomy",
                "slug": "lawsafrica-subjects",
                "children": [
                    {
                        "name": "Estates, Trusts and Succession",
                        "slug": "lawsafrica-subjects-estates-trusts-and-succession",
                        "children": [],
                    },
                    {
                        "name": "Money and Business",
                        "slug": "lawsafrica-subjects-money-and-business",
                        "children": [
                            {
                                "name": "Banking",
                                "slug": "lawsafrica-subjects-money-and-business-banking",
                                "children": [],
                            },
                            {
                                "name": "Finance",
                                "slug": "lawsafrica-subjects-money-and-business-finance",
                                "children": [],
                            },
                        ],
                    },
                    {
                        "name": "People and Work",
                        "slug": "lawsafrica-subjects-people-and-work",
                        "children": [
                            {
                                "name": "Children",
                                "slug": "lawsafrica-subjects-people-and-work-children",
                                "children": [],
                            },
                            {
                                "name": "Communications",
                                "slug": "lawsafrica-subjects-people-and-work-communications",
                                "children": [],
                            },
                        ],
                    },
                ],
            },
        ], response.data['results'])
