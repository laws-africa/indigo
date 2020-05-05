from django.test.utils import override_settings
from sass_processor.processor import SassProcessor
from rest_framework.test import APITestCase

from indigo_content_api.tests.v1.test_content_api import ContentAPIV1TestMixin


# Ensure the processor runs during tests. It doesn't run when DEBUG=False (ie. during testing),
# but during testing we haven't compiled assets
SassProcessor.processor_enabled = True


class ContentAPIV2TestMixin(ContentAPIV1TestMixin):
    api_path = '/api/v2/akn'

    def test_published_json(self):
        response = self.client.get(self.api_path + '/za/act/2014/10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/akn/za/act/2014/10')

        response = self.client.get(self.api_path + '/za/act/2014/10.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/akn/za/act/2014/10')

        response = self.client.get(self.api_path + '/za/act/2014/10/eng.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/akn/za/act/2014/10')

    def test_latest_expression_in_listing(self):
        # a listing should only include the most recent expression of a document
        # with different expression dates
        response = self.client.get(self.api_path + '/za/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')

        docs = [d for d in response.data['results'] if d['frbr_uri'] == '/akn/za/act/2010/1']
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['expression_date'], '2012-02-02')

    def test_published_points_in_time(self):
        response = self.client.get(self.api_path + '/za/act/2010/1/eng@.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/akn/za/act/2010/1')
        self.assertEqual(response.data['points_in_time'], [
            {
                'date': '2011-01-01',
                'expressions': [{
                    'url': 'http://' + self.api_host + self.api_path + '/za/act/2010/1/eng@2011-01-01',
                    'expression_frbr_uri': '/akn/za/act/2010/1/eng@2011-01-01',
                    'language': 'eng',
                    'title': 'Act with amendments',
                    'expression_date': '2011-01-01',
                }]
            },
            {
                'date': '2012-02-02',
                'expressions': [{
                    'url': 'http://' + self.api_host + self.api_path + '/za/act/2010/1/eng@2012-02-02',
                    'expression_frbr_uri': '/akn/za/act/2010/1/eng@2012-02-02',
                    'language': 'eng',
                    'title': 'Act with amendments',
                    'expression_date': '2012-02-02',
                }]
            }
        ])

    def test_published_repealed(self):
        response = self.client.get(self.api_path + '/za/act/2001/8/eng.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['repeal'], {
            'date': '2014-02-12',
            'repealing_uri': '/akn/za/act/2014/10',
            'repealing_title': 'Water Act',
        })

    def test_published_search_perms(self):
        old = self.api_path
        self.api_path = '/api/v2'
        super(ContentAPIV2TestMixin, self).test_published_search_perms()
        self.api_path = old

    def test_published_search(self):
        old = self.api_path
        self.api_path = '/api/v2'
        super(ContentAPIV2TestMixin, self).test_published_search()
        self.api_path = old

    def test_published_html_akn_prefixed(self):
        response = self.client.get(self.api_path + '/za/act/2010/1.html')
        self.assertNotIn('/resolver/resolve/za', response.content.decode('utf-8'))
        self.assertIn('/resolver/resolve/akn/za', response.content.decode('utf-8'))

    def test_published_publication_document(self):
        response = self.client.get(self.api_path + '/za/act/2014/10/eng@2014-02-12.json')
        self.assertEqual(response.status_code, 200)

        # this deliberately doesn't use the API path, it uses the app path which allows
        # us to make this public
        self.assertEqual(response.data['publication_document']['url'], 'http://localhost:8000/works/akn/za/act/2014/10/media/publication/za-act-2014-10-publication-document.pdf')


# Disable pipeline storage - see https://github.com/cyberdelia/django-pipeline/issues/277
@override_settings(STATICFILES_STORAGE='pipeline.storage.PipelineStorage', PIPELINE_ENABLED=False)
class ContentAPIV2Test(ContentAPIV2TestMixin, APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'work', 'published', 'colophon', 'attachments',
                'commencements']
