from django.test import testcases, override_settings
from django.contrib.auth.models import User

from pinax.badges.registry import badges


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SocialViewsTest(testcases.TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor']

    def test_contributor_page(self):
        response = self.client.get('/contributors/')
        self.assertEqual(response.status_code, 200)

    def test_profile_page(self):
        user = User.objects.first()
        response = self.client.get('/contributors/{}'.format(user.username))
        self.assertEqual(response.status_code, 200)

    def test_edit_user_profile(self):
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 302)

        self.assertTrue(self.client.login(username='email@example.com', password='password'))
        try:
            response = self.client.get('/accounts/profile/')
            self.assertEqual(response.status_code, 200)
        finally:
            self.client.logout()

    def test_activity_page(self):
        user = User.objects.first()
        response = self.client.get('/contributors/{}/activity/'.format(user.username))
        self.assertEqual(response.status_code, 200)

    def test_bage_list_page(self):
        response = self.client.get('/badges/')
        self.assertEqual(response.status_code, 200)

    def test_badge_detail_page(self):
        badge = list(badges.registry.values())[0]
        response = self.client.get('/badges/{}/'.format(badge.slug))
        self.assertEqual(response.status_code, 200)
