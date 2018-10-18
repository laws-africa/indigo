import datetime

from django.test import testcases, override_settings
import reversion

from indigo_api.models import Work


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WorksTest(testcases.TestCase):
    fixtures = ['countries', 'work', 'user', 'editor', 'drafts', 'published']

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

    def test_create_edit_delete_amendment(self):
        work = Work.objects.get(frbr_uri='/za/act/2010/1')

        # create
        response = self.client.post('/works/za/act/2010/1/amendments/new', {'amending_work': '2', 'date': '2012-02-02'})
        self.assertEqual(response.status_code, 302)
        amendment = work.amendments.all()[0]
        self.assertIsNotNone(amendment.created_by_user)
        self.assertIsNotNone(amendment.updated_by_user)

        self.assertEqual(amendment.amending_work.id, 2)
        self.assertEqual(amendment.date.strftime("%Y-%m-%d"), '2012-02-02')

        # edit
        response = self.client.post('/works/za/act/2010/1/amendments/%s' % amendment.id, {'date': '2013-03-03'})
        self.assertEqual(response.status_code, 302)
        amendment = work.amendments.all()[0]
        self.assertEqual(amendment.date.strftime("%Y-%m-%d"), '2013-03-03')

        # expressions/documents should have updated
        docs = list(work.expressions().filter(expression_date=datetime.date(2013, 3, 3)).all())
        self.assertEqual(len(docs), 1)

        # move the expressions out the way for the next test
        for doc in docs:
            doc.expression_date = work.publication_date
            doc.save()

        # delete
        response = self.client.post('/works/za/act/2010/1/amendments/%s' % amendment.id, {'delete': ''})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(work.amendments.all()), 0)

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

    def test_create_new_pit_with_existing(self):
        response = self.client.post('/works/za/act/2014/10/points-in-time/new', {
            'expression_date': '2019-01-01',
            'language': '1',
        })
        self.assertEqual(response.status_code, 302)

        work = Work.objects.get(frbr_uri='/za/act/2014/10')
        doc = work.expressions().filter(expression_date=datetime.date(2019, 1, 1)).first()
        self.assertEqual(doc.draft, True)
        self.assertIn('tester', doc.content)

    def test_create_pit_without_existing(self):
        response = self.client.post('/works/za/act/2014/10/points-in-time/new', {
            'expression_date': '2019-01-01',
            'language': '2',
        })
        self.assertEqual(response.status_code, 302)

        work = Work.objects.get(pk=1)
        doc = work.expressions().filter(expression_date=datetime.date(2019, 1, 1)).first()
        self.assertEqual(doc.draft, True)
        self.assertNotIn('tester', doc.content)
