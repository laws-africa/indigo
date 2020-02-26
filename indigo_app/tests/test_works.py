# -*- coding: utf-8 -*-

import datetime

from django.test import testcases, override_settings
from django_webtest import WebTest
from django.contrib.auth.models import User
from webtest import Upload

import reversion

from indigo_app.views.works import WorkViewBase
from indigo_api.models import Work, Commencement, Amendment, ArbitraryExpressionDate


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WorksTest(testcases.TestCase):
    fixtures = ['countries', 'user', 'taxonomies', 'work', 'editor', 'drafts', 'published', 'publications']

    def setUp(self):
        self.assertTrue(self.client.login(username='email@example.com', password='password'))

    def test_new_work(self):
        response = self.client.get('/places/za/works/new/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/places/za-cpt/works/new/')
        self.assertEqual(response.status_code, 200)

    def test_edit_page(self):
        response = self.client.get('/works/za/act/2014/10/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/works/za-cpt/act/2005/1/')
        self.assertEqual(response.status_code, 200)

    def test_related_page(self):
        response = self.client.get('/works/za/act/2014/10/related/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/works/za-cpt/act/2005/1/related/')
        self.assertEqual(response.status_code, 200)

    def test_amendments_page(self):
        response = self.client.get('/works/za/act/2014/10/amendments/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/works/za/act/2010/1/amendments/')
        self.assertEqual(response.status_code, 200)

    def test_create_edit_delete_amendment(self):
        work = Work.objects.get(frbr_uri='/za/act/2010/1')
        # the fixtures create two amendments, one at 2011-01-01 and one at 2012-02-02
        amendment = list(work.amendments.all())[-1]

        # edit
        response = self.client.post('/works/za/act/2010/1/amendments/%s' % amendment.id, {'date': '2013-03-03'})
        self.assertEqual(response.status_code, 302)
        amendment = list(work.amendments.all())[-1]
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
        self.assertEqual(len(work.amendments.all()), 1)

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

    def test_get_work_timeline(self):
        view = WorkViewBase()
        work = Work.objects.get(pk=1)
        work.assent_date = datetime.date(2014, 3, 20)
        amendment = Amendment(amended_work_id=1, amending_work_id=2, date='2019-01-01', created_by_user_id=1)
        amendment.save()

        consolidation = ArbitraryExpressionDate(work=work, date='2018-01-01', created_by_user_id=1)
        consolidation.save()

        timeline = WorkViewBase.get_work_timeline(view, work)
        # most recent event first
        self.assertEqual(timeline[0]['date'], datetime.date(2019, 1, 1))
        self.assertEqual(timeline[0]['amendments'][0].date, datetime.date(2019, 1, 1))
        self.assertEqual(timeline[0]['initial'], False)

        # consolidation
        self.assertEqual(timeline[1]['date'], datetime.date(2018, 1, 1))
        self.assertEqual(timeline[1]['consolidations'][0].date, datetime.date(2018, 1, 1))
        self.assertEqual(timeline[1]['initial'], False)

        # publication date on fixture
        self.assertEqual(timeline[2]['date'], datetime.date(2014, 4, 2))
        self.assertEqual(timeline[2]['publication_date'], True)
        self.assertEqual(timeline[2]['initial'], True)

        # assent date (oldest)
        self.assertEqual(timeline[-1]['date'], datetime.date(2014, 3, 20))
        self.assertEqual(timeline[-1]['assent_date'], True)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WorksWebTest(WebTest):
    """ Test that uses https://github.com/django-webtest/django-webtest to help us
    fill and submit forms.
    """
    fixtures = ['countries', 'user', 'taxonomies', 'work', 'editor', 'drafts', 'published', 'commencements']

    def setUp(self):
        self.app.set_user(User.objects.get(username='email@example.com'))

    def test_create_work_with_publication(self):
        form = self.app.get('/places/za/works/new/').forms['edit-work-form']
        form['work-title'] = "Title"
        form['work-frbr_uri'] = '/za/act/2019/5'
        form['work-publication_date'] = '2019-02-01'
        form['work-publication_document_file'] = Upload('pub.pdf', b'data', 'application/pdf')
        response = form.submit()
        self.assertRedirects(response, '/works/za/act/2019/5/', fetch_redirect_response=False)

    def test_publication_date_updates_documents(self):
        """ Changing the work's publication date should also updated documents
        that are linked to the initial publication date.
        """
        work = Work.objects.get(frbr_uri='/za/act/1945/1')
        initial = work.initial_expressions()
        self.assertEqual(initial[0].publication_date.strftime('%Y-%m-%d'), "1945-10-12")

        form = self.app.get('/works%s/edit/' % work.frbr_uri).forms['edit-work-form']
        form['work-publication_date'] = '1945-12-12'
        response = form.submit()
        self.assertRedirects(response, '/works%s/' % work.frbr_uri, fetch_redirect_response=False)

        work = Work.objects.get(frbr_uri='/za/act/1945/1')
        initial = list(work.initial_expressions().all())
        self.assertEqual(initial[0].publication_date.strftime('%Y-%m-%d'), "1945-12-12")
        self.assertEqual(len(initial), 1)

    def test_create_work_with_commencement_date_and_commencing_work(self):
        form = self.app.get('/places/za/works/new/').forms['edit-work-form']
        form['work-title'] = "Commenced Work With Date and Commencing Work"
        form['work-frbr_uri'] = '/za/act/2020/3'
        form['work-commenced'] = True
        form['work-commencement_date'] = '2020-02-11'
        form['work-commencing_work'] = 6
        form.submit()
        work = Work.objects.get(frbr_uri='/za/act/2020/3')
        commencement = Commencement.objects.get(commenced_work=work)
        commencing_work = Work.objects.get(pk=6)
        self.assertTrue(work.commenced)
        self.assertEqual(commencement.commencing_work, commencing_work)
        self.assertEqual(commencement.date, datetime.date(2020, 2, 11))
        self.assertTrue(commencement.main)
        self.assertTrue(commencement.all_provisions)

    def test_create_work_without_commencement_date_but_with_commencing_work(self):
        form = self.app.get('/places/za/works/new/').forms['edit-work-form']
        form['work-title'] = "Commenced Work With Commencing Work but No Date"
        form['work-frbr_uri'] = '/za/act/2020/4'
        form['work-commenced'] = True
        form['work-commencing_work'] = 6
        form.submit()
        work = Work.objects.get(frbr_uri='/za/act/2020/4')
        commencement = Commencement.objects.get(commenced_work=work)
        commencing_work = Work.objects.get(pk=6)
        self.assertTrue(work.commenced)
        self.assertEqual(commencement.commencing_work, commencing_work)
        self.assertIsNone(commencement.date)
        self.assertTrue(commencement.main)
        self.assertTrue(commencement.all_provisions)

    def test_create_work_without_commencement_date_or_commencing_work(self):
        form = self.app.get('/places/za/works/new/').forms['edit-work-form']
        form['work-title'] = "Commenced Work Without Date or Commencing Work"
        form['work-frbr_uri'] = '/za/act/2020/5'
        form['work-commenced'] = True
        form.submit()
        work = Work.objects.get(frbr_uri='/za/act/2020/5')
        commencement = Commencement.objects.get(commenced_work=work)
        self.assertTrue(work.commenced)
        self.assertIsNone(commencement.commencing_work)
        self.assertIsNone(commencement.date)
        self.assertTrue(commencement.main)
        self.assertTrue(commencement.all_provisions)

    def test_create_uncommenced_work(self):
        form = self.app.get('/places/za/works/new/').forms['edit-work-form']
        form['work-title'] = "Uncommenced Work"
        form['work-frbr_uri'] = '/za/act/2020/6'
        form.submit()
        work = Work.objects.get(frbr_uri='/za/act/2020/6')
        self.assertFalse(work.commenced)
        self.assertFalse(work.commencements.all())

    def test_edit_uncommenced_work_to_commence(self):
        uncommenced_work = Work.objects.get(pk=2)
        self.assertFalse(uncommenced_work.commenced)

        form = self.app.get(f'/works{uncommenced_work.frbr_uri}/edit/').forms['edit-work-form']
        form['work-commenced'] = True
        form['work-commencement_date'] = '2020-02-11'
        form['work-commencing_work'] = 6
        form.submit()

        work = Work.objects.get(pk=2)
        commencing_work = Work.objects.get(pk=6)
        self.assertTrue(work.commenced)
        commencement = Commencement.objects.get(commenced_work=work)
        self.assertEqual(commencement.commencing_work, commencing_work)
        self.assertEqual(commencement.date, datetime.date(2020, 2, 11))
