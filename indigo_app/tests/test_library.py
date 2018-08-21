from django.test import testcases, override_settings


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class LibraryTest(testcases.TestCase):
    fixtures = ['countries', 'work', 'user', 'editor', 'drafts', 'published']

    def setUp(self):
        self.assertTrue(self.client.login(username='email@example.com', password='password'))

    def test_library(self):
        response = self.client.get('/library/za/')
        self.assertEqual(response.status_code, 200)
