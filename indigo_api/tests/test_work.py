import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.core.exceptions import ValidationError

from indigo_api.models import Document, Work, Country, Amendment, ArbitraryExpressionDate, Commencement


class WorkTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomy_topics', 'work', 'published', 'drafts', 'commencements']

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

    def test_possible_expression_dates_future_commencement(self):
        """ Use the consolidation date if the commencement date is in the future and the publication date is not known.
        """
        # the work commences on 2016-07-15
        self.work.publication_date = None
        consolidation = ArbitraryExpressionDate(work=self.work, date='2010-01-01', created_by_user_id=1)
        consolidation.save()
        self.assertEqual(
            [
                {'date': datetime.date(2010, 1, 1),
                 'amendment': False,
                 'consolidation': True,
                 'initial': True},
            ],
            self.work.possible_expression_dates()
        )

    def test_no_initial_date(self):
        self.work.publication_date = None
        self.work.commencements.all().delete()
        self.assertEqual([],
            self.work.possible_expression_dates()
        )

    def test_update_uncommenced_work(self):
        # start state: an uncommenced work
        uncommenced_work = Work.objects.create(frbr_uri='/akn/za/act/2024/1', country_id=1)
        self.assertFalse(uncommenced_work.commenced)

        # later: a commencement notice and a commencement are created
        commencement_notice = Work.objects.create(frbr_uri='/akn/za/act/gn/2024/10', country_id=1)
        Commencement.objects.create(commenced_work=uncommenced_work, commencing_work=commencement_notice)

        # the work should now be commenced
        self.assertTrue(uncommenced_work.commenced)

    def test_incoming_related_works(self):
        commences = Work.objects.create(
            country=self.work.country,
            frbr_uri="/akn/za/act/2023/99-commences",
            title="commences",
        )
        Commencement.objects.create(commenced_work=self.work, commencing_work=commences, date=datetime.date.today())

        amends = Work.objects.create(
            country=self.work.country,
            frbr_uri="/akn/za/act/2023/99-amends",
            title="amends",
        )
        Amendment.objects.create(amended_work=self.work, amending_work=amends, date=datetime.date.today(),
                                 created_by_user=User.objects.first())

        repeals = Work.objects.create(
            country=self.work.country,
            frbr_uri="/akn/za/act/2023/99-repeals",
            title="repeals",
        )
        self.work.repealed_by = repeals
        self.work.repealed_date = '2025-04-09'
        self.work.save()

        # this will be ignored
        child = Work.objects.create(
            country=self.work.country,
            frbr_uri="/akn/za/act/2023/99-child",
            title="child",
            parent_work=self.work,
        )

        self.assertEqual(
            [amends, commences, repeals],
            sorted(Work.get_incoming_related_works([self.work]), key=lambda x: x.title)
        )
