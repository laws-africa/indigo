# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase

from indigo_api.models import Work


class CommencementsTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work', 'published', 'drafts', 'commencements']

    def setUp(self):
        self.work = Work.objects.get(id=11)

    def test_commenceable_provisions(self):
        """ Provisions that don't yet exist at a given date shouldn't be included,
            but provisions that did exist and have been removed should be. """
        provisions_all = [p.id for p in self.work.commenceable_provisions()]
        provisions_before_publication = [p.id for p in self.work.commenceable_provisions(date=datetime.date(2019, 1, 1))]
        provisions_at_publication = [p.id for p in self.work.commenceable_provisions(date=datetime.date(2020, 1, 1))]
        provisions_at_future_date = [p.id for p in self.work.commenceable_provisions(date=datetime.date(2021, 1, 1))]
        provisions_at_later_expression_date = [p.id for p in self.work.commenceable_provisions(date=datetime.date(2022, 1, 1))]

        self.assertEqual(provisions_all, ['sec_1', 'sec_2', 'sec_3', 'sec_4', 'sec_5', 'sec_6', 'sec_7'])
        self.assertEqual(provisions_before_publication, [])
        self.assertEqual(provisions_at_publication, ['sec_1', 'sec_2', 'sec_3', 'sec_4'])
        self.assertEqual(provisions_at_future_date, ['sec_1', 'sec_2', 'sec_3', 'sec_4'])
        self.assertEqual(provisions_at_later_expression_date, ['sec_1', 'sec_2', 'sec_3', 'sec_4', 'sec_5', 'sec_6', 'sec_7'])

    def test_uncommenced_provisions(self):
        """ Provisions that don't yet exist at a given date shouldn't be included,
            but provisions that did exist and have been removed should be. """
        uncommenced_provisions_all = [p.id for p in self.work.uncommenced_provisions()]
        uncommenced_provisions_before_publication = [p.id for p in self.work.uncommenced_provisions(date=datetime.date(2019, 1, 1))]
        uncommenced_provisions_at_publication = [p.id for p in self.work.uncommenced_provisions(date=datetime.date(2020, 1, 1))]
        uncommenced_provisions_at_future_date = [p.id for p in self.work.uncommenced_provisions(date=datetime.date(2021, 1, 1))]
        uncommenced_provisions_at_later_expression_date = [p.id for p in self.work.uncommenced_provisions(date=datetime.date(2022, 1, 1))]

        self.assertEqual(uncommenced_provisions_all, ['sec_4', 'sec_6'])
        self.assertEqual(uncommenced_provisions_before_publication, [])
        self.assertEqual(uncommenced_provisions_at_publication, ['sec_4'])
        self.assertEqual(uncommenced_provisions_at_future_date, ['sec_4'])
        self.assertEqual(uncommenced_provisions_at_later_expression_date, ['sec_4', 'sec_6'])

    def test_commencements_relevant_to_current_expression(self):
        """ Future commencements should be included even if only one of their `provisions` exists at the given date,
         but not if there's no overlap.
        """
        commencements_before_publication = [c.id for c in self.work.commencements_relevant_to_current_expression(date=datetime.date(2019, 1, 1))]
        commencements_at_publication = [c.id for c in self.work.commencements_relevant_to_current_expression(date=datetime.date(2020, 1, 1))]
        commencements_at_future_date = [c.id for c in self.work.commencements_relevant_to_current_expression(date=datetime.date(2021, 1, 1))]
        commencements_at_later_expression_date = [c.id for c in self.work.commencements_relevant_to_current_expression(date=datetime.date(2022, 1, 1))]

        self.assertEqual(commencements_before_publication, [])
        self.assertEqual(commencements_at_publication, [4, 5, 7])
        self.assertEqual(commencements_at_future_date, [4, 5, 7])
        self.assertEqual(commencements_at_later_expression_date, [4, 5, 6, 7])
