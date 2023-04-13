from django.test import TestCase

from indigo_api.models import Work, Country
from indigo_za.work_detail import WorkDetailZA


class WorkDetailZATestCase(TestCase):
    fixtures = ['languages_data', 'countries']

    def setUp(self):
        self.plugin = WorkDetailZA()
        self.country = Country.objects.get(pk=1)

    def test_numbered_title_bylaw(self):
        work = Work(frbr_uri='/akn/za-cpt/act/by-law/2020/problem-property', country=self.country)
        self.assertIsNone(self.plugin.work_numbered_title(work))

    def test_numbered_title_ministerial_order(self):
        work = Work(frbr_uri='/akn/za/act/mo/2020/acsa-covid-19', country=self.country)
        self.assertIsNone(self.plugin.work_numbered_title(work))

    def test_numbered_title_rules(self):
        work = Work(frbr_uri='/akn/za/act/rules/2016/national-assembly', country=self.country)
        self.assertIsNone(self.plugin.work_numbered_title(work))
