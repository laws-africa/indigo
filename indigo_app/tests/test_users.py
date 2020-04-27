import datetime

from django.test import testcases, override_settings
from django_webtest import WebTest
from django.contrib.auth.models import User
from webtest import Upload

import reversion

from indigo_api.models import Work


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class UsersWebTest(WebTest):
    fixtures = ['languages_data', 'countries', 'user', 'editor']

    def setUp(self):
        self.app.set_user(User.objects.get(username='email@example.com'))

    def test_edit_account(self):
        form = self.app.get('/accounts/profile/').forms[0]
        form['first_name'] = 'Joe'
        form['last_name'] = 'User'
        form['username'] = 'joeuser'
        form['country'] = '1'
        response = form.submit()
        self.assertRedirects(response, '/accounts/profile/')

        user = User.objects.get(username='joeuser')
        self.assertEqual(user.first_name, 'Joe')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.editor.country.id, 1)

    def test_edit_account_api_new_token(self):
        form = self.app.get('/accounts/profile/api/').forms[0]
        api_token = form['api_token'].value

        # generates a new api token
        response = form.submit()
        self.assertRedirects(response, '/accounts/profile/api/')

        form = self.app.get('/accounts/profile/api/').forms[0]
        self.assertNotEqual(api_token, form['api_token'].value)
