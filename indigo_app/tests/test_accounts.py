import os

from django.test import testcases, override_settings


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class LibraryTest(testcases.TestCase):
    fixtures = ['countries', 'user', 'editor']

    def setUp(self):
        os.environ['RECAPTCHA_TESTING'] = 'True'

    def tearDown(self):
        os.environ['RECAPTCHA_TESTING'] = 'False'

    def test_login_page(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/accounts/login/', {'login': 'email@example.com', 'password': 'password'})
        self.assertEqual(response.status_code, 302)

    def test_signup_page(self):
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/accounts/signup/', {
            'email': 'new-user@example.com',
            'password1': 'password',
            'password2': 'password',
            'accepted_terms': 'on',
            'first_name': 'First',
            'last_name': 'Last',
            'country': '1',
            'g-recaptcha-response': 'PASSED'
        })
        self.assertEqual(response.status_code, 302)

    def test_account_page(self):
        self.assertTrue(self.client.login(username='email@example.com', password='password'))

        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/accounts/password/change/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/accounts/email/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/accounts/social/connections/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/accounts/profile/api/')
        self.assertEqual(response.status_code, 200)
