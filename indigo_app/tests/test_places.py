from django.contrib.auth.models import User
from django.test import testcases, override_settings
from django_webtest import WebTest


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PlacesTest(testcases.TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomy_topics', 'work', 'editor', 'drafts', 'published']

    def setUp(self):
        self.assertTrue(self.client.login(username='email@example.com', password='password'))

    def test_place_detail(self):
        response = self.client.get('/places/za')
        self.assertEqual(response.status_code, 200)

    def test_place_activity(self):
        response = self.client.get('/places/za/activity')
        self.assertEqual(response.status_code, 200)

    def test_place_settings(self):
        response = self.client.get('/places/za/settings')
        self.assertEqual(response.status_code, 200)

    def test_place_settings_no_perms(self):
        self.client.logout()
        response = self.client.get('/places/za/settings')
        self.assertEqual(response.status_code, 302)

    def test_place_localities(self):
        response = self.client.get('/places/za/localities')
        self.assertEqual(response.status_code, 200)

    def test_place_works(self):
        response = self.client.get('/places/za/works')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/places/za/works/facets')
        self.assertEqual(response.status_code, 200)

    def test_all_place_works(self):
        response = self.client.get('/places/all/works')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/places/all/works/facets')
        self.assertEqual(response.status_code, 200)

    def test_all_place_tasks_404(self):
        response = self.client.get('/places/all/tasks')
        self.assertEqual(response.status_code, 404)

    def test_place_works_xlsx(self):
        response = self.client.get('/places/za/works?format=xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PlacesWebTest(WebTest):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomy_topics', 'work', 'editor', 'drafts', 'tasks']

    def setUp(self):
        self.app.set_user(User.objects.get(username='email@example.com'))

    def test_place_settings(self):
        form = self.app.get('/places/za/settings').forms[0]
        form['spreadsheet_url'].value = 'https://docs.google.com/spreadsheets/d/1a2o-842lGliSwlLo3gSbYSRbaOYu-2PZhC1rOf8MgA4/'
        form['as_at_date'].value = '2019-01-01'
        form['styleguide_url'].value = 'https://docs.laws.africa/editing-a-document/importing-a-document'
        form = form.submit().follow().forms[0]
        self.assertEqual(form['spreadsheet_url'].value, 'https://docs.google.com/spreadsheets/d/1a2o-842lGliSwlLo3gSbYSRbaOYu-2PZhC1rOf8MgA4/')
        self.assertEqual(form['as_at_date'].value, '2019-01-01')
        self.assertEqual(form['styleguide_url'].value, 'https://docs.laws.africa/editing-a-document/importing-a-document')

    def test_place_settings_spreadsheet_url_cleaned(self):
        form = self.app.get('/places/za/settings').forms[0]
        form['spreadsheet_url'].value = 'https://docs.google.com/spreadsheets/d/12auCcgbt6WYUsqt8m2uyRDQUYrYS-9iDmRDd-QqvqNQ/edit#gid=1003990263'
        form = form.submit().follow().forms[0]
        self.assertEqual(form['spreadsheet_url'].value, 'https://docs.google.com/spreadsheets/d/12auCcgbt6WYUsqt8m2uyRDQUYrYS-9iDmRDd-QqvqNQ/')

    def test_place_settings_spreadsheet_url_bad(self):
        form = self.app.get('/places/za/settings').forms[0]
        form['spreadsheet_url'].value = 'https://docs.google.com/spreadsheets/d/12auCcgbt6WYUsqt8m2uyRDQUYrYS-9iDmRDd-QqvqNQ'
        form['as_at_date'].value = '2020-01-01'
        form['styleguide_url'].value = 'https://docs.laws.africa/style-guides/south-african-by-laws'
        form = form.submit().forms[0]
        # form should reload with all current values plus error message
        self.assertIn('Please enter a valid Google Sheets URL, such as https://docs.google.com/spreadsheets/d/ABCXXX/', form.html.text)
        self.assertEqual(form['spreadsheet_url'].value, 'https://docs.google.com/spreadsheets/d/12auCcgbt6WYUsqt8m2uyRDQUYrYS-9iDmRDd-QqvqNQ')
        self.assertEqual(form['as_at_date'].value, '2020-01-01')
        self.assertEqual(form['styleguide_url'].value, 'https://docs.laws.africa/style-guides/south-african-by-laws')
