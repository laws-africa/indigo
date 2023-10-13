from nose.tools import *  # noqa
from django.test import TestCase
from datetime import date

from indigo_api.models import Document, Work, Amendment, Language, Country, User
from indigo_api.tests.fixtures import *  # noqa


class DocumentTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'taxonomy_topics', 'work', 'published', 'drafts', 'commencements']

    def setUp(self):
        self.work = Work.objects.get(id=1)
        self.eng = Language.for_code('eng')

    def test_empty_document(self):
        d = Document(work=self.work)
        self.assertIsNotNone(d.doc)

    def test_change_title(self):
        user = User.objects.get(pk=1)
        d = Document.objects.create(title="Title", frbr_uri="/akn/za/act/1980/01", work=self.work, expression_date=date(2001, 1, 1), language=self.eng, created_by_user=user, updated_by_user=user)
        d.save()
        id = d.id
        self.assertTrue(d.document_xml.startswith('<akomaNtoso'))

        d2 = Document.objects.get(id=id)
        self.assertEqual(d.title, d2.title)

    def test_set_content(self):
        d = Document()
        d.work = self.work
        d.content = document_fixture('γνωρίζω')

        assert_equal(d.frbr_uri, '/akn/za/act/1900/1')
        assert_equal(d.country, 'za')
        assert_equal(d.doc.publication_date, date(2005, 7, 24))

    def test_expression_date(self):
        d = Document(work=self.work)
        d.content = document_fixture('test')
        d.expression_date = date(2014, 1, 1)
        assert_equal(d.expression_date, date(2014, 1, 1))

    def test_empty_expression_date(self):
        d = Document(work=self.work)
        d.content = document_fixture('test')
        d.expression_date = ''
        assert_equal(d.expression_date, '')

        d.expression_date = None
        assert_equal(d.expression_date, None)

    def test_inherit_from_work(self):
        user = User.objects.get(pk=1)
        w = Work.objects.create(frbr_uri='/akn/za/act/2009/test', title='Test document', country=Country.for_code('za'), created_by_user=user)
        d = Document(work=w, expression_date='2011-02-01', language=self.eng, created_by_user=user)
        d.save()

        d = Document.objects.get(pk=d.id)
        assert_equal(w.frbr_uri, d.frbr_uri)
        assert_equal(w.title, d.title)

    def test_repeal_from_work(self):
        rep = Work.objects.get(id=2)
        d = Document.objects.get(id=1)
        w = d.work
        w.repealed_by = rep
        w.repealed_date = rep.publication_date
        w.save()

        d = Document.objects.get(id=1)
        assert_equal(d.repeal.repealing_uri, rep.frbr_uri)
        assert_equal(d.repeal.repealing_title, rep.title)
        assert_equal(d.repeal.date, rep.publication_date)

    def test_amendments_from_work(self):
        amending = Work.objects.get(id=1)
        # this work has two docs:
        #  2 - expression date: 2011-01-01
        #  3 - expression date: 2012-02-02
        amended = Work.objects.get(id=3)
        d = date(2011, 12, 10)

        # this will impact only document id 3
        user = User.objects.get(pk=1)
        a = Amendment(amending_work=amending, amended_work=amended, date=d, created_by_user=user)
        a.save()

        doc = Document.objects.get(id=2)
        # only the pre-existing amendment event
        assert_equal(len(doc.amendment_events()), 1)

        doc = Document.objects.get(id=3)
        events = list(doc.amendment_events())
        # one new in addition to the two previous ones
        assert_equal(len(events), 3)
        assert_equal(events[1].amending_uri, amending.frbr_uri)
        assert_equal(events[1].amending_title, amending.title)
        assert_equal(events[1].date, d)

    def test_is_latest(self):
        d = Document(work=self.work)
        d.expression_date = ''
        self.assertFalse(d.is_latest())
        d.expression_date = None
        self.assertFalse(d.is_latest())
        d = Document.objects.get(id=2)
        self.assertFalse(d.is_latest())
        d = Document.objects.get(id=3)
        self.assertTrue(d.is_latest())

    def test_valid_until(self):
        d = Document(work=self.work)
        d.expression_date = ''
        self.assertIsNone(d.valid_until())
        d.expression_date = None
        self.assertIsNone(d.valid_until())
        d = Document.objects.get(id=2)
        self.assertEqual(date(2012, 2, 1), d.valid_until())
        d = Document.objects.get(id=3)
        self.assertEqual(date(2019, 1, 1), d.valid_until())

    def test_is_consolidation(self):
        d = Document(work=self.work)
        self.assertFalse(d.is_consolidation())
        d = Document.objects.get(id=2)
        self.assertFalse(d.is_consolidation())
        d = Document.objects.get(id=3)
        self.assertFalse(d.is_consolidation())
        d = Document.objects.get(id=8)
        self.assertTrue(d.is_consolidation())

    def test_consolidation_note(self):
        d = Document(work=self.work)
        self.assertEqual('A general consolidation note that applies to all consolidations in this place.', d.work.consolidation_note())
        d = Document.objects.get(id=4)
        self.assertEqual('A special consolidation note just for this work', d.work.consolidation_note())

    def test_commencement_description(self):
        # fairly straightforward work with a single commencement
        d = Document(work=self.work)
        description = d.work.commencement_description_internal()
        self.assertEqual('commencement', description.type)
        self.assertEqual('single', description.subtype)
        self.assertEqual('Commenced on 2016-07-15', description.description)
        self.assertEqual(date(2016, 7, 15), description.date)
        self.assertEqual('', description.note)
        self.assertEqual('', description.by_frbr_uri)
        self.assertEqual('', description.by_title)
        self.assertEqual(None, description.by_work)
        # format date for external use
        description = d.work.commencement_description_external()
        self.assertEqual('Commenced on 15 July 2016', description.description)

        # uncommenced work
        d = Document.objects.get(id=7)
        description = d.work.commencement_description()
        self.assertEqual('uncommenced', description.subtype)
        self.assertEqual('Not commenced', description.description)

        # multiple commencements
        d = Document.objects.get(id=104)
        description = d.work.commencement_description()
        self.assertEqual('commencement', description.type)
        self.assertEqual('multiple', description.subtype)
        self.assertEqual('There are multiple commencements', description.description)
        self.assertEqual(None, description.date)
        self.assertEqual('', description.note)
        self.assertEqual('', description.by_frbr_uri)
        self.assertEqual('', description.by_title)
        self.assertEqual(None, description.by_work)

        # but not all commencements apply to earlier points in time
        description = d.work.commencement_description(commencements=d.commencements_relevant_at_expression_date(),
                                                      has_uncommenced_provisions=bool(d.work.all_uncommenced_provision_ids(d.expression_date)))
        self.assertEqual('commencement', description.type)
        self.assertEqual('single', description.subtype)
        self.assertEqual('Commenced on 1 March 2023 by', description.description)
        self.assertEqual(date(2023, 3, 1), description.date)
        self.assertEqual('Note: See section 4(2)', description.note)
        self.assertEqual('/akn/za/act/gn/2023/1', description.by_frbr_uri)
        self.assertEqual('Commencing work', description.by_title)
        self.assertEqual(Work.objects.get(pk=15), description.by_work)
