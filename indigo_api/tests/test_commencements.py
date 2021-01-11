# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase

from indigo_api.models import Document, Work


class WorkTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work', 'published', 'drafts', 'commencements']

    def setUp(self):
        self.work = Work.objects.get(id=11)
        self.document = Document.objects.get(pk=21)

    def test_commenceable_provisions(self):
        provisions_all = [p.id for p in self.document.work.commenceable_provisions()]
        provisions_before_publication = [p.id for p in self.document.work.commenceable_provisions(date=datetime.date(2019, 1, 1))]
        provisions_at_publication = [p.id for p in self.document.work.commenceable_provisions(date=datetime.date(2020, 1, 1))]
        provisions_at_future_date = [p.id for p in self.document.work.commenceable_provisions(date=datetime.date(2021, 1, 1))]
        provisions_at_later_expression_date = [p.id for p in self.document.work.commenceable_provisions(date=datetime.date(2022, 1, 1))]

        self.assertEqual(provisions_all, ['sec_1', 'sec_2', 'sec_3', 'sec_4', 'sec_5'])
        self.assertEqual(provisions_before_publication, [])
        self.assertEqual(provisions_at_publication, ['sec_1', 'sec_2', 'sec_3', 'sec_4'])
        self.assertEqual(provisions_at_future_date, ['sec_1', 'sec_2', 'sec_3', 'sec_4'])
        self.assertEqual(provisions_at_later_expression_date, ['sec_1', 'sec_2', 'sec_3', 'sec_4', 'sec_5'])

    def test_uncommenced_provisions(self):
        uncommenced_provisions_all = [p.id for p in self.document.work.uncommenced_provisions()]
        uncommenced_provisions_before_publication = [p.id for p in self.document.work.uncommenced_provisions(date=datetime.date(2019, 1, 1))]
        uncommenced_provisions_at_publication = [p.id for p in self.document.work.uncommenced_provisions(date=datetime.date(2020, 1, 1))]
        uncommenced_provisions_at_future_date = [p.id for p in self.document.work.uncommenced_provisions(date=datetime.date(2021, 1, 1))]
        uncommenced_provisions_at_later_expression_date = [p.id for p in self.document.work.uncommenced_provisions(date=datetime.date(2022, 1, 1))]

        self.assertEqual(uncommenced_provisions_all, ['sec_4', 'sec_6'])
        self.assertEqual(uncommenced_provisions_before_publication, [])
        self.assertEqual(uncommenced_provisions_at_publication, ['sec_4'])
        self.assertEqual(uncommenced_provisions_at_future_date, ['sec_4'])
        self.assertEqual(uncommenced_provisions_at_later_expression_date, ['sec_4', 'sec_6'])
