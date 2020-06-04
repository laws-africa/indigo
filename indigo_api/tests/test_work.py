# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.core.exceptions import ValidationError

from indigo_api.models import Document, Work, Country, Amendment, ArbitraryExpressionDate


class WorkTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work', 'published', 'drafts', 'commencements']

    def setUp(self):
        self.work = Work.objects.get(id=1)

    def test_cascade_frbr_uri_changes(self):
        document = Document.objects.get(pk=20)
        self.assertEqual(document.frbr_uri, '/akn/za/act/1945/1')

        document.work.frbr_uri = '/akn/za/act/2999/1'
        document.work.save()

        document = Document.objects.get(pk=20)
        self.assertEqual(document.frbr_uri, '/akn/za/act/2999/1')

    def test_commencement_as_pit_date(self):
        """ When the publication date is unknown, fall back
        to the commencement date as a possible point in time.
        """
        self.work.publication_date = None
        events = self.work.possible_expression_dates()
        initial = events[-1]
        self.assertTrue(initial['initial'])
        self.assertEqual(initial['date'], self.work.commencement_date)

    def test_validates_uri(self):
        country = Country.objects.first()

        work = Work(frbr_uri='bad', country=country)
        self.assertRaises(ValidationError, work.full_clean)

        work = Work(frbr_uri='', country=country)
        self.assertRaises(ValidationError, work.full_clean)

    def test_possible_expression_dates_basic(self):
        self.work.publication_date = datetime.date(2018, 2, 23)
        amendment = Amendment(amended_work=self.work, amending_work_id=2, date='2019-09-13', created_by_user_id=1)
        amendment.save()
        amendment = Amendment(amended_work=self.work, amending_work_id=2, date='2020-12-05', created_by_user_id=1)
        amendment.save()
        dates = self.work.possible_expression_dates()
        self.assertEqual(
            dates,
            [
                {'date': datetime.date(2020, 12, 5),
                 'amendment': True,
                 'consolidation': False,
                 'initial': False},
                {'date': datetime.date(2019, 9, 13),
                 'amendment': True,
                 'consolidation': False,
                 'initial': False},
                {'date': datetime.date(2018, 2, 23),
                 'initial': True},
            ]
        )

    def test_possible_expression_dates_commencement(self):
        self.work.publication_date = None
        # the commencements fixture commences work 1 on 2016-07-15
        amendment = Amendment(amended_work=self.work, amending_work_id=2, date='2020-09-13', created_by_user_id=1)
        amendment.save()
        amendment = Amendment(amended_work=self.work, amending_work_id=2, date='2018-12-05', created_by_user_id=1)
        amendment.save()
        dates = self.work.possible_expression_dates()
        self.assertEqual(
            dates,
            [
                {'date': datetime.date(2020, 9, 13),
                 'amendment': True,
                 'consolidation': False,
                 'initial': False},
                {'date': datetime.date(2018, 12, 5),
                 'amendment': True,
                 'consolidation': False,
                 'initial': False},
                {'date': datetime.date(2016, 7, 15),
                 'initial': True},
            ]
        )

    def test_possible_expression_dates_amendment_first(self):
        self.work.publication_date = datetime.date(2017, 2, 23)
        amendment = Amendment(amended_work=self.work, amending_work_id=2, date='2020-09-13', created_by_user_id=1)
        amendment.save()
        amendment = Amendment(amended_work=self.work, amending_work_id=2, date='2016-12-05', created_by_user_id=1)
        amendment.save()
        dates = self.work.possible_expression_dates()
        self.assertEqual(
            dates,
            [
                {'date': datetime.date(2020, 9, 13),
                 'amendment': True,
                 'consolidation': False,
                 'initial': False},
                {'date': datetime.date(2017, 2, 23),
                 'initial': True},
                {'date': datetime.date(2016, 12, 5),
                 'amendment': True,
                 'consolidation': False,
                 'initial': False},
            ]
        )

    def test_possible_expression_dates_amended_on_publication(self):
        self.work.publication_date = datetime.date(2017, 2, 23)
        amendment = Amendment(amended_work=self.work, amending_work_id=2, date='2020-09-13', created_by_user_id=1)
        amendment.save()
        amendment = Amendment(amended_work=self.work, amending_work_id=2, date='2017-02-23', created_by_user_id=1)
        amendment.save()
        dates = self.work.possible_expression_dates()
        self.assertEqual(
            dates,
            [
                {'date': datetime.date(2020, 9, 13),
                 'amendment': True,
                 'consolidation': False,
                 'initial': False},
                {'date': datetime.date(2017, 2, 23),
                 'amendment': True,
                 'consolidation': False,
                 'initial': True},
            ]
        )

    def test_possible_expression_dates_consolidation(self):
        self.work.publication_date = datetime.date(2017, 2, 23)
        consolidation = ArbitraryExpressionDate(work=self.work, date='2020-09-13', created_by_user_id=1)
        consolidation.save()
        amendment = Amendment(amended_work=self.work, amending_work_id=2, date='2018-12-05', created_by_user_id=1)
        amendment.save()
        dates = self.work.possible_expression_dates()
        self.assertEqual(
            dates,
            [
                {'date': datetime.date(2020, 9, 13),
                 'amendment': False,
                 'consolidation': True,
                 'initial': False},
                {'date': datetime.date(2018, 12, 5),
                 'amendment': True,
                 'consolidation': False,
                 'initial': False},
                {'date': datetime.date(2017, 2, 23),
                 'initial': True},
            ]
        )
