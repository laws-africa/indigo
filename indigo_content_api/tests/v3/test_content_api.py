from django.test.utils import override_settings
from rest_framework.test import APITestCase
from sass_processor.processor import SassProcessor

from indigo_content_api.tests.v2.test_content_api import ContentAPIV2TestMixin

# Ensure the processor runs during tests. It doesn't run when DEBUG=False (ie. during testing),
# but during testing we haven't compiled assets
SassProcessor.processor_enabled = True


class ContentAPIV3TestMixin(ContentAPIV2TestMixin):
    api_path = '/api/v3'
    api_host = 'testserver'

    def test_commenced(self):
        response = self.client.get(self.api_path + '/akn/za/act/2010/1.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['commenced'], True)
        self.assertEqual(response.data['commencement_date'], '2010-06-01')

        # detailed commencements are given separately in v3
        self.assertNotIn('commencements', response.data.keys())
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/commencements.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([dict(x) for x in response.data['commencements']], [{
            'commencing_title': None,
            'commencing_frbr_uri': None,
            'date': '2010-06-01',
            'provisions': [],
            'main': True,
            'note': 'A note',
            'all_provisions': True,
        }])

    def test_taxonomies(self):
        response = self.client.get(self.api_path + '/akn/za/act/1880/1.json')
        self.assertEqual(response.status_code, 200)

        # 'taxonomies' is not included in v3
        self.assertNotIn('taxonomies', response.data.keys())

        self.assertEqual(
            ['lawsafrica-subject-areas-money-and-business'],
            response.data['taxonomy_topics'])

    def test_timeline(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10/timeline.json')
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response.accepted_media_type)
        # TODO: fill this in
        self.assertEqual({}, response.data['timeline'])


# Disable pipeline storage - see https://github.com/cyberdelia/django-pipeline/issues/277
@override_settings(STATICFILES_STORAGE='pipeline.storage.PipelineStorage', PIPELINE_ENABLED=False)
class ContentAPIV3Test(ContentAPIV3TestMixin, APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'work', 'published', 'colophon',
                'attachments', 'commencements', 'taxonomy_topics']
