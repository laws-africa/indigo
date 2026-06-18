from rest_framework.test import APITestCase
from django.test.utils import override_settings

from indigo_api.models import Work
from indigo_app.tests.utils import TEST_STORAGES


@override_settings(STORAGES=TEST_STORAGES)
class WorkAPITest(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomy_topics', 'work', 'drafts', 'published']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')

    def test_prevent_delete(self):
        work = Work.objects.get(pk=7)

        self.assertRedirects(self.client.post('/works%s/delete' % work.frbr_uri), '/works%s/edit/' % work.frbr_uri)

        # delete linked documents
        work.expressions().delete()

        # now can delete
        self.assertRedirects(self.client.post('/works%s/delete' % work.frbr_uri), '/places/za')

    def test_filters(self):
        response = self.client.get('/api/works?country=za')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        response = self.client.get('/api/works?country=xy')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])
