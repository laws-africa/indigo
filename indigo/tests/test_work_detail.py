from django.test import TestCase
from django.utils.translation import override

from indigo.analysis.work_detail import BaseWorkDetail
from indigo_api.models import Work, Country, ChapterNumber


class BaseWorkDetailTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'subtype']

    def setUp(self):
        self.country = Country.objects.first()
        self.plugin = BaseWorkDetail()

    def test_numbered_title_simple(self):
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/1999/32"
        )
        self.assertEqual('Act 32 of 1999', self.plugin.work_numbered_title(work))
        with override('fr', deactivate=True):
            self.assertEqual('Loi 32 de 1999', self.plugin.work_numbered_title(work))

    def test_numbered_title_caps(self):
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/gn/1999/r32"
        )
        self.assertEqual('Government Notice R32 of 1999', self.plugin.work_numbered_title(work))

    def test_numbered_title_none(self):
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/1999/constitution"
        )
        self.assertIsNone(self.plugin.work_numbered_title(work))

        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/2012/constitution-seventeenth-amendment"
        )
        self.assertIsNone(self.plugin.work_numbered_title(work))

    def test_numbered_title_ignore_subtype(self):
        plugin = BaseWorkDetail()
        plugin.no_numbered_title_subtypes = ['gn']
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/gn/1999/32"
        )
        self.assertIsNone(plugin.work_numbered_title(work))

    def test_numbered_title_non_act(self):
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/bill/1999/32"
        )
        self.assertEqual('Bill 32 of 1999', self.plugin.work_numbered_title(work))

    def test_numbered_title_chapter_simple(self):
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/1999/32"
        )
        ChapterNumber.objects.create(number='123', work=work)
        self.assertEqual('Chapter 123', self.plugin.work_numbered_title(work))
        # but adding a second one without a date gives us nothing to work with
        ChapterNumber.objects.create(number='456', work=work)
        self.assertEqual('Act 32 of 1999', self.plugin.work_numbered_title(work))

    def test_numbered_title_chapter_two_same_start_date(self):
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/1999/32"
        )
        ChapterNumber.objects.create(number='123', work=work, validity_start_date='2025-06-03')
        self.assertEqual('Chapter 123', self.plugin.work_numbered_title(work))
        # but adding a second one at the same date gives us nothing to work with
        ChapterNumber.objects.create(number='456', work=work, validity_start_date='2025-06-03')
        self.assertEqual('Act 32 of 1999', self.plugin.work_numbered_title(work))

    def test_numbered_title_chapter_different_start_dates(self):
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/1999/32"
        )
        ChapterNumber.objects.create(number='123', work=work, validity_start_date='2025-06-03')
        self.assertEqual('Chapter 123', self.plugin.work_numbered_title(work))
        ChapterNumber.objects.create(number='456', work=work, validity_start_date='2025-06-04')
        self.assertEqual('Chapter 456', self.plugin.work_numbered_title(work))
        # a third one without a date gets ignored
        ChapterNumber.objects.create(number='789', work=work)
        self.assertEqual('Chapter 456', self.plugin.work_numbered_title(work))

    def test_numbered_title_chapter_mix_start_and_end_dates_1(self):
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/1999/32"
        )
        ChapterNumber.objects.create(number='123', work=work, validity_start_date='2025-06-03')
        self.assertEqual('Chapter 123', self.plugin.work_numbered_title(work))
        # a new one without a start date gets ignored
        ChapterNumber.objects.create(number='456', work=work, validity_end_date='2025-06-02')
        self.assertEqual('Chapter 123', self.plugin.work_numbered_title(work))
        # another one at an older start date
        ChapterNumber.objects.create(number='789', work=work, validity_start_date='2025-06-02')
        self.assertEqual('Chapter 123', self.plugin.work_numbered_title(work))
        # another one at the same start date -- back to numbered title
        ChapterNumber.objects.create(number='789', work=work, validity_start_date='2025-06-03')
        self.assertEqual('Act 32 of 1999', self.plugin.work_numbered_title(work))

    def test_numbered_title_chapter_mix_start_and_end_dates_2(self):
        work = Work.objects.create(
            country=self.country,
            title="test",
            frbr_uri="/akn/za/act/1999/32"
        )
        ChapterNumber.objects.create(number='123', work=work, validity_start_date='2025-06-03')
        self.assertEqual('Chapter 123', self.plugin.work_numbered_title(work))
        # a new one without a start date gets ignored
        ChapterNumber.objects.create(number='456', work=work, validity_end_date='2025-06-02')
        self.assertEqual('Chapter 123', self.plugin.work_numbered_title(work))
        # another one at a more recent start date
        ChapterNumber.objects.create(number='789', work=work, validity_start_date='2025-06-04')
        self.assertEqual('Chapter 789', self.plugin.work_numbered_title(work))
