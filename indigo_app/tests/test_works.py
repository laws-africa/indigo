from django.test import testcases, override_settings


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WorksTest(testcases.TestCase):
    fixtures = ['work', 'user']

    def setUp(self):
        self.assertTrue(self.client.login(username='email@example.com', password='password'))

    def test_new_work(self):
        response = self.client.get('/works/new/')
        self.assertEqual(response.status_code, 200)

    def test_edit_page(self):
        response = self.client.get('/works/za/act/2014/10/')
        self.assertEqual(response.status_code, 200)

    def test_related_page(self):
        response = self.client.get('/works/za/act/2014/10/related/')
        self.assertEqual(response.status_code, 200)

    def test_amendments_page(self):
        response = self.client.get('/works/za/act/2014/10/amendments/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/works/za/act/2010/1/amendments/')
        self.assertEqual(response.status_code, 200)

    def test_import_view(self):
        response = self.client.get('/works/za/act/2014/10/import/')
        self.assertEqual(response.status_code, 200)
