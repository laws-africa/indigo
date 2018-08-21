from django.test import testcases, override_settings
import reversion

from indigo_api.models import Work


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WorksTest(testcases.TestCase):
    fixtures = ['countries', 'work', 'editor', 'user']

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

    def test_permission_to_restore_work_version(self):
        response = self.client.get('/works/za/act/2014/10/')
        self.assertEqual(response.status_code, 200)

        # make a change
        work = Work.objects.get(pk=1)
        with reversion.revisions.create_revision():
            work.title = 'changed title'
            work.save()

        # this user doesn't have permission to edit works
        self.client.logout()
        self.assertTrue(self.client.login(username='non-deleter@example.com', password='password'))

        # try revert it
        version = work.versions().last()
        response = self.client.post('/works/za/act/2014/10/revisions/%s/restore' % version.id)
        self.assertEqual(response.status_code, 403)

        # this user can
        self.assertTrue(self.client.login(username='email@example.com', password='password'))
        response = self.client.post('/works/za/act/2014/10/revisions/%s/restore' % version.id)
        self.assertEqual(response.status_code, 302)
