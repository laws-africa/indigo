import datetime

from django.test import testcases, override_settings
from django_webtest import WebTest
from django.contrib.auth.models import User
from webtest import Upload

import reversion

from indigo_app.views.works import WorkViewBase
from indigo_api.models import Work, Commencement, Amendment, ArbitraryExpressionDate, Country, Document


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WorksTest(testcases.TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'taxonomy_topics', 'work', 'editor', 'drafts', 'published', 'publications', 'commencements']

    def setUp(self):
        self.assertTrue(self.client.login(username='email@example.com', password='password'))

    def test_new_work(self):
        response = self.client.get('/places/za/works/new')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/places/za-cpt/works/new')
        self.assertEqual(response.status_code, 200)

    def test_edit_page(self):
        response = self.client.get('/works/akn/za/act/2014/10/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/works/akn/za-cpt/act/2005/1/')
        self.assertEqual(response.status_code, 200)

    def test_related_page(self):
        response = self.client.get('/works/akn/za/act/2014/10/related/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/works/akn/za-cpt/act/2005/1/related/')
        self.assertEqual(response.status_code, 200)

    def test_amendments_page(self):
        response = self.client.get('/works/akn/za/act/2014/10/amendments/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/works/akn/za/act/2010/1/amendments/')
        self.assertEqual(response.status_code, 200)

    def test_create_edit_delete_amendment(self):
        work = Work.objects.get(frbr_uri='/akn/za/act/2010/1')
        # the fixtures create two amendments, one at 2011-01-01 and one at 2012-02-02
        amendment = list(work.amendments.all())[-1]

        # edit
        response = self.client.post('/works/akn/za/act/2010/1/amendments/%s' % amendment.id, {'date': '2013-03-03'})
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
        response = self.client.post('/works/akn/za/act/2010/1/amendments/%s' % amendment.id, {'delete': ''})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(work.amendments.all()), 1)

    def test_import_view(self):
        response = self.client.get('/works/akn/za/act/2014/10/import/')
        self.assertEqual(response.status_code, 200)

    def test_permission_to_restore_work_version(self):
        response = self.client.get('/works/akn/za/act/2014/10/')
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
        response = self.client.post('/works/akn/za/act/2014/10/revisions/%s/restore' % version.id)
        self.assertEqual(response.status_code, 403)

        # this user can
        self.assertTrue(self.client.login(username='email@example.com', password='password'))
        response = self.client.post('/works/akn/za/act/2014/10/revisions/%s/restore' % version.id)
        self.assertEqual(response.status_code, 302)

    def test_create_new_pit_with_existing(self):
        response = self.client.post('/works/akn/za/act/2014/10/points-in-time/new', {
            'expression_date': '2019-01-01',
            'language': '1',
        })
        self.assertEqual(response.status_code, 302)

        work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        doc = work.expressions().filter(expression_date=datetime.date(2019, 1, 1)).first()
        self.assertEqual(doc.draft, True)
        self.assertIn('tester', doc.content)

    def test_create_pit_without_existing(self):
        response = self.client.post('/works/akn/za/act/2014/10/points-in-time/new', {
            'expression_date': '2019-01-01',
            'language': '2',
        })
        self.assertEqual(response.status_code, 302)

        work = Work.objects.get(pk=1)
        doc = work.expressions().filter(expression_date=datetime.date(2019, 1, 1)).first()
        self.assertEqual(doc.draft, True)
        self.assertNotIn('tester', doc.content)

    def test_get_work_timeline(self):
        work = Work.objects.get(pk=1)
        work.assent_date = datetime.date(2014, 3, 20)
        amendment = Amendment(amended_work_id=1, amending_work_id=2, date='2019-01-01', created_by_user_id=1)
        amendment.save()

        consolidation = ArbitraryExpressionDate(work=work, date='2018-01-01', created_by_user_id=1)
        consolidation.save()

        view = WorkViewBase()
        timeline = view.get_work_timeline(work)
        self.assertEqual(5, len(timeline))

        # most recent event first
        self.assertEqual(datetime.date(2019, 1, 1), timeline[0].date)
        self.assertEqual(False, timeline[0].initial)
        self.assertEqual(1, len(timeline[0].events))
        event = timeline[0].events[0]
        self.assertEqual('amendment', event.type)
        self.assertEqual('Amended by', event.description)
        self.assertEqual('/akn/za/act/1998/2', event.by_frbr_uri)
        self.assertEqual('Test Act', event.by_title)
        self.assertEqual('', event.note)
        self.assertEqual(amendment, event.related)

        # consolidation
        self.assertEqual(datetime.date(2018, 1, 1), timeline[1].date)
        self.assertEqual(False, timeline[1].initial)
        self.assertEqual(1, len(timeline[1].events))
        event = timeline[1].events[0]
        self.assertEqual('consolidation', event.type)
        self.assertEqual('Consolidation', event.description)
        self.assertEqual('', event.by_frbr_uri)
        self.assertEqual('', event.by_title)
        self.assertEqual('', event.note)
        self.assertEqual(consolidation, event.related)

        # commencement date on fixture
        self.assertEqual(datetime.date(2016, 7, 15), timeline[2].date)
        self.assertEqual(False, timeline[2].initial)
        self.assertEqual(1, len(timeline[2].events))
        event = timeline[2].events[0]
        self.assertEqual('commencement', event.type)
        self.assertEqual('Commenced', event.description)
        self.assertEqual('', event.by_frbr_uri)
        self.assertEqual('', event.by_title)
        self.assertEqual('', event.note)
        self.assertEqual(Commencement.objects.get(pk=1), event.related)

        # publication date on fixture
        self.assertEqual(datetime.date(2014, 4, 2), timeline[3].date)
        self.assertEqual(True, timeline[3].initial)
        self.assertEqual(1, len(timeline[3].events))
        event = timeline[3].events[0]
        self.assertEqual('publication', event.type)
        self.assertEqual('Published in Government Gazette 12345', event.description)
        self.assertEqual('', event.by_frbr_uri)
        self.assertEqual('', event.by_title)
        self.assertEqual('', event.note)
        self.assertEqual(None, event.related)

        # assent date (oldest)
        self.assertEqual(datetime.date(2014, 3, 20), timeline[4].date)
        self.assertEqual(False, timeline[4].initial)
        self.assertEqual(1, len(timeline[4].events))
        event = timeline[4].events[0]
        self.assertEqual('assent', event.type)
        self.assertEqual('Assented to', event.description)
        self.assertEqual('', event.by_frbr_uri)
        self.assertEqual('', event.by_title)
        self.assertEqual('', event.note)
        self.assertEqual(None, event.related)

    def test_get_work_timeline_multiple_amendments(self):
        work = Work.objects.get(pk=1)
        work.assent_date = datetime.date(2014, 3, 20)

        act_2_of_1998 = Work.objects.get(pk=2)
        amendment_1 = Amendment(amended_work_id=1, amending_work=act_2_of_1998, date='2019-01-01', created_by_user_id=1)
        amendment_1.save()

        gn_1_of_1900 = Work(frbr_uri='/akn/za/act/gn/1900/1', country_id=1, created_by_user_id=1)
        gn_1_of_1900.save()
        amendment_2 = Amendment(amended_work_id=1, amending_work=gn_1_of_1900, date='2019-01-01', created_by_user_id=1)
        amendment_2.save()

        act_30_of_1900 = Work(frbr_uri='/akn/za/act/1900/30', country_id=1, created_by_user_id=1)
        act_30_of_1900.save()
        amendment_3 = Amendment(amended_work_id=1, amending_work=act_30_of_1900, date='2019-01-01', created_by_user_id=1)
        amendment_3.save()

        act_12_of_1900 = Work(frbr_uri='/akn/za/act/1900/12', country_id=1, created_by_user_id=1)
        act_12_of_1900.save()
        amendment_4 = Amendment(amended_work_id=1, amending_work=act_12_of_1900, date='2019-01-01', created_by_user_id=1)
        amendment_4.save()

        act_2_of_1900 = Work(frbr_uri='/akn/za/act/1900/2', country_id=1, created_by_user_id=1)
        act_2_of_1900.save()
        amendment_5 = Amendment(amended_work_id=1, amending_work=act_2_of_1900, date='2019-01-01', created_by_user_id=1)
        amendment_5.save()

        act_1_of_1900 = Work.objects.get(pk=6)
        amendment_6 = Amendment(amended_work_id=1, amending_work=act_1_of_1900, date='2019-01-01', created_by_user_id=1)
        amendment_6.save()

        act_1_of_1998 = Work(frbr_uri='/akn/za/act/1998/1', country_id=1, created_by_user_id=1)
        act_1_of_1998.save()
        amendment_7 = Amendment(amended_work_id=1, amending_work=act_1_of_1998, date='2019-01-01', created_by_user_id=1)
        amendment_7.save()

        view = WorkViewBase()
        timeline = view.get_work_timeline(work)
        # self.assertEqual(3, len(timeline))
        self.assertEqual(4, len(timeline))
        self.assertEqual(7, len(timeline[0].events))

        event = timeline[0].events[0]
        self.assertEqual('amendment', event.type)
        self.assertEqual('Amended by', event.description)
        self.assertEqual('/akn/za/act/1900/1', event.by_frbr_uri)
        self.assertEqual('Test suite document fixture act', event.by_title)
        self.assertEqual(amendment_6, event.related)
        self.assertEqual('', event.note)

        event = timeline[0].events[1]
        self.assertEqual('amendment', event.type)
        self.assertEqual('Amended by', event.description)
        self.assertEqual('/akn/za/act/1900/2', event.by_frbr_uri)
        self.assertEqual('(untitled)', event.by_title)
        self.assertEqual(amendment_5, event.related)
        self.assertEqual('', event.note)

        event = timeline[0].events[2]
        self.assertEqual('amendment', event.type)
        self.assertEqual('Amended by', event.description)
        self.assertEqual('/akn/za/act/1900/12', event.by_frbr_uri)
        self.assertEqual('(untitled)', event.by_title)
        self.assertEqual(amendment_4, event.related)
        self.assertEqual('', event.note)

        event = timeline[0].events[3]
        self.assertEqual('amendment', event.type)
        self.assertEqual('Amended by', event.description)
        self.assertEqual('/akn/za/act/1900/30', event.by_frbr_uri)
        self.assertEqual('(untitled)', event.by_title)
        self.assertEqual(amendment_3, event.related)
        self.assertEqual('', event.note)

        event = timeline[0].events[4]
        self.assertEqual('amendment', event.type)
        self.assertEqual('Amended by', event.description)
        self.assertEqual('/akn/za/act/gn/1900/1', event.by_frbr_uri)
        self.assertEqual('(untitled)', event.by_title)
        self.assertEqual(amendment_2, event.related)
        self.assertEqual('', event.note)

        event = timeline[0].events[5]
        self.assertEqual('amendment', event.type)
        self.assertEqual('Amended by', event.description)
        self.assertEqual('/akn/za/act/1998/1', event.by_frbr_uri)
        self.assertEqual('(untitled)', event.by_title)
        self.assertEqual(amendment_7, event.related)
        self.assertEqual('', event.note)

        event = timeline[0].events[6]
        self.assertEqual('amendment', event.type)
        self.assertEqual('Amended by', event.description)
        self.assertEqual('/akn/za/act/1998/2', event.by_frbr_uri)
        self.assertEqual('Test Act', event.by_title)
        self.assertEqual(amendment_1, event.related)
        self.assertEqual('', event.note)

    def test_get_work_timeline_squash_commencement_and_amendment_by_same_work(self):
        view = WorkViewBase()
        work = Work.objects.get(pk=17)
        timeline = view.get_work_timeline(work)

        # publication at 2023-10-01; amendment at 2023-11-01
        self.assertEqual(2, len(timeline))
        self.assertEqual(datetime.date(2023, 11, 1), timeline[0].date)
        # just the one event
        self.assertEqual(1, len(timeline[0].events))

        event = timeline[0].events[0]
        self.assertEqual('amendment', event.type)
        self.assertEqual('Amended by', event.description)
        self.assertEqual(Amendment.objects.get(pk=7), event.related)
        self.assertEqual('A work that both amends and commences another work on the same date', event.by_title)
        self.assertEqual('/akn/za/act/2023/11', event.by_frbr_uri)
        # but we do have the note from the commencement
        self.assertEqual('Commencement note: See section 12 of Act 11 of 2023', event.note)

    def test_get_work_timeline_dont_squash_commencement_and_amendment_by_different_works(self):
        view = WorkViewBase()
        work = Work.objects.get(pk=19)
        timeline = view.get_work_timeline(work)

        # publication at 2023-10-01; amendment and commencement at 2023-11-01
        self.assertEqual(2, len(timeline))
        self.assertEqual(datetime.date(2023, 11, 1), timeline[0].date)
        # two events
        self.assertEqual(2, len(timeline[0].events))

        # amendment
        event_1 = timeline[0].events[0]
        self.assertEqual('amendment', event_1.type)
        self.assertEqual('Amended by', event_1.description)
        self.assertEqual(Amendment.objects.get(pk=8), event_1.related)
        self.assertEqual('A work that both amends and commences another work on the same date', event_1.by_title)
        self.assertEqual('/akn/za/act/2023/11', event_1.by_frbr_uri)
        # no note on the amendment when the commencement is separate
        self.assertEqual('', event_1.note)

        # commencement
        event_2 = timeline[0].events[1]
        self.assertEqual('commencement', event_2.type)
        self.assertEqual('Commenced by', event_2.description)
        self.assertEqual(Commencement.objects.get(pk=12), event_2.related)
        self.assertEqual('Commencement notice', event_2.by_title)
        self.assertEqual('/akn/za/act/gn/2023/21', event_2.by_frbr_uri)
        self.assertEqual('Note: See section 1', event_2.note)

    def test_no_publication_document(self):
        # this work has no publication document
        resp = self.client.get('/works/akn/za/act/2010/1/media/publication/')
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get('/works/akn/za/act/2010/1/media/publication/test.pdf')
        self.assertEqual(resp.status_code, 404)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WorksWebTest(WebTest):
    """ Test that uses https://github.com/django-webtest/django-webtest to help us
    fill and submit forms.
    """
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'taxonomy_topics', 'work', 'editor', 'drafts', 'published', 'commencements']

    def setUp(self):
        self.app.set_user(User.objects.get(username='email@example.com'))

    def test_create_work_with_publication(self):
        form = self.app.get('/places/za/works/new').forms['edit-work-form']
        form['work-title'] = "Title"
        form['work-frbr_uri'] = '/akn/za/act/2019/5'
        form['work-frbr_doctype'] = 'act'
        form['work-frbr_date'] = '2019'
        form['work-frbr_number'] = '5'
        form['work-publication_date'] = '2019-02-01'
        form['work-publication_document_file'] = Upload('pub.pdf', b'data', 'application/pdf')
        response = form.submit()
        self.assertRedirects(response, '/works/akn/za/act/2019/5/', fetch_redirect_response=False)

    def test_publication_date_updates_documents(self):
        """ Changing the work's publication date should also updated documents
        that are linked to the initial publication date.
        """
        work = Work.objects.get(frbr_uri='/akn/za/act/1945/1')
        initial = work.initial_expressions()
        self.assertEqual(initial[0].publication_date.strftime('%Y-%m-%d'), "1945-10-12")

        form = self.app.get('/works%s/edit/' % work.frbr_uri).forms['edit-work-form']
        form['work-publication_date'] = '1945-12-12'
        response = form.submit()
        self.assertRedirects(response, '/works%s/' % work.frbr_uri, fetch_redirect_response=False)

        work = Work.objects.get(frbr_uri='/akn/za/act/1945/1')
        initial = list(work.initial_expressions().all())
        self.assertEqual(initial[0].publication_date.strftime('%Y-%m-%d'), "1945-12-12")
        self.assertEqual(len(initial), 1)

    def test_create_work_with_commencement_date_and_commencing_work(self):
        form = self.app.get('/places/za/works/new').forms['edit-work-form']
        form['work-title'] = "Commenced Work With Date and Commencing Work"
        form['work-frbr_uri'] = '/akn/za/act/2020/3'
        form['work-commenced'] = True
        form['work-commencement_date'] = '2020-02-11'
        form['work-commencing_work'] = 6
        form.submit()
        work = Work.objects.get(frbr_uri='/akn/za/act/2020/3')
        commencement = Commencement.objects.get(commenced_work=work)
        commencing_work = Work.objects.get(pk=6)
        self.assertTrue(work.commenced)
        self.assertEqual(commencement.commencing_work, commencing_work)
        self.assertEqual(commencement.date, datetime.date(2020, 2, 11))
        self.assertTrue(commencement.main)
        self.assertTrue(commencement.all_provisions)

    def test_create_work_without_commencement_date_but_with_commencing_work(self):
        form = self.app.get('/places/za/works/new').forms['edit-work-form']
        form['work-title'] = "Commenced Work With Commencing Work but No Date"
        form['work-frbr_uri'] = '/akn/za/act/2020/4'
        form['work-frbr_doctype'] = 'act'
        form['work-frbr_date'] = '2020'
        form['work-frbr_number'] = '4'
        form['work-commenced'] = True
        form['work-commencing_work'] = 6
        form.submit()
        work = Work.objects.get(frbr_uri='/akn/za/act/2020/4')
        commencement = Commencement.objects.get(commenced_work=work)
        commencing_work = Work.objects.get(pk=6)
        self.assertTrue(work.commenced)
        self.assertEqual(commencement.commencing_work, commencing_work)
        self.assertIsNone(commencement.date)
        self.assertTrue(commencement.main)
        self.assertTrue(commencement.all_provisions)

    def test_create_work_without_commencement_date_or_commencing_work(self):
        form = self.app.get('/places/za/works/new').forms['edit-work-form']
        form['work-title'] = "Commenced Work Without Date or Commencing Work"
        form['work-frbr_uri'] = '/akn/za/act/2020/5'
        form['work-frbr_doctype'] = 'act'
        form['work-frbr_date'] = '2020'
        form['work-frbr_number'] = '5'
        form['work-commenced'] = True
        form.submit()
        work = Work.objects.get(frbr_uri='/akn/za/act/2020/5')
        commencement = Commencement.objects.get(commenced_work=work)
        self.assertTrue(work.commenced)
        self.assertIsNone(commencement.commencing_work)
        self.assertIsNone(commencement.date)
        self.assertTrue(commencement.main)
        self.assertTrue(commencement.all_provisions)

    def test_create_uncommenced_work(self):
        form = self.app.get('/places/za/works/new').forms['edit-work-form']
        form['work-title'] = "Uncommenced Work"
        form['work-frbr_doctype'] = 'act'
        form['work-frbr_date'] = '2020'
        form['work-frbr_number'] = '6'
        form.submit()
        work = Work.objects.get(frbr_uri='/akn/za/act/2020/6')
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

    def test_work_title_changes_documents_with_same_title(self):
        doc = Document.objects.get(pk=4)
        self.assertEqual(doc.title, doc.work.title)

        form = self.app.get(f'/works{doc.work.frbr_uri}/edit/').forms['edit-work-form']
        form['work-title'] = "New Title"
        form.submit()

        doc.refresh_from_db()
        self.assertEqual("New Title", doc.title)

    def test_work_title_ignores_documents_with_different_title(self):
        doc = Document.objects.get(pk=4)
        self.assertEqual(doc.title, doc.work.title)

        doc.title = "Different Title"
        doc.save()

        form = self.app.get(f'/works{doc.work.frbr_uri}/edit/').forms['edit-work-form']
        form['work-title'] = "New Title"
        form.submit()

        doc.refresh_from_db()
        self.assertEqual("Different Title", doc.title)

    def test_create_non_act_work(self):
        form = self.app.get('/places/za/works/new').forms['edit-work-form']
        form['work-title'] = "Title"
        form['work-frbr_doctype'] = 'statement'
        form['work-frbr_date'] = '2018-02-02'
        form['work-frbr_number'] = '123-45'
        response = form.submit()
        self.assertRedirects(response, '/works/akn/za/statement/2018-02-02/123-45/', fetch_redirect_response=False)
