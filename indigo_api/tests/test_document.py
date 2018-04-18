# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from django.test import TestCase
from datetime import date

from indigo_api.models import Document, Work, Amendment
from indigo_api.tests.fixtures import *  # noqa


class DocumentTestCase(TestCase):
    fixtures = ['work', 'published']

    def setUp(self):
        self.work = Work.objects.get(id=1)

    def test_empty_document(self):
        d = Document()
        self.assertIsNotNone(d.doc)

    def test_change_title(self):
        d = Document.objects.create(title="Title", frbr_uri="/za/act/1980/01", work=self.work)
        d.save()
        id = d.id
        self.assertTrue(d.document_xml.startswith('<akomaNtoso'))

        d2 = Document.objects.get(id=id)
        self.assertEqual(d.title, d2.title)

    def test_set_content(self):
        d = Document()
        d.content = document_fixture(u'γνωρίζω')

        assert_equal(d.frbr_uri, '/za/act/1900/1')
        assert_equal(d.country, 'za')
        assert_equal(d.doc.publication_date, date(2005, 7, 24))

    def test_expression_date(self):
        d = Document()
        d.content = document_fixture('test')
        d.expression_date = date(2014, 1, 1)
        assert_equal(d.expression_date, date(2014, 1, 1))

    def test_empty_expression_date(self):
        d = Document()
        d.content = document_fixture('test')
        d.expression_date = ''
        assert_equal(d.expression_date, '')

        d.expression_date = None
        assert_equal(d.expression_date, None)

    def test_inherit_from_work(self):
        w = Work.objects.create(frbr_uri='/za/act/2009/test', title='Test document')
        d = Document(work=w, expression_date='2011-02-01')
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

        # this will impact only work 2
        a = Amendment(amending_work=amending, amended_work=amended, date=d)
        a.save()

        doc = Document.objects.get(id=2)
        assert_equal(doc.amendments, [])

        doc = Document.objects.get(id=3)
        assert_equal(len(doc.amendments), 1)
        assert_equal(doc.amendments[0].amending_uri, amending.frbr_uri)
        assert_equal(doc.amendments[0].amending_title, amending.title)
        assert_equal(doc.amendments[0].date, d)
