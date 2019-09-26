from django.test import testcases, override_settings


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PlacesTest(testcases.TestCase):
    fixtures = ['countries', 'user', 'taxonomies', 'work', 'editor', 'drafts', 'published']

    def setUp(self):
        self.assertTrue(self.client.login(username='email@example.com', password='password'))

    def test_place_detail(self):
        response = self.client.get('/places/za/')
        self.assertEqual(response.status_code, 200)

    def test_place_activity(self):
        response = self.client.get('/places/za/activity')
        self.assertEqual(response.status_code, 200)

    def test_place_metrics(self):
        response = self.client.get('/places/za/metrics')
        self.assertEqual(response.status_code, 200)

    def test_place_settings(self):
        response = self.client.get('/places/za/metrics')
        self.assertEqual(response.status_code, 200)

    def test_place_settings_no_perms(self):
        self.client.logout()
        response = self.client.get('/places/za/metrics')
        self.assertEqual(response.status_code, 302)

    def test_place_localities(self):
        response = self.client.get('/places/za/localities')
        self.assertEqual(response.status_code, 200)
