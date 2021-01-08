# -*- coding: utf-8 -*-
from django.test import TestCase

from indigo_api.models import Work
from indigo_za.work_detail import WorkDetailZA


class WorkDetailZATestCase(TestCase):
    def setUp(self):
        self.plugin = WorkDetailZA()

    def test_numbered_title_bylaw(self):
        work = Work(frbr_uri='/akn/za-cpt/act/by-law/2020/problem-property')
        self.assertIsNone(self.plugin.work_numbered_title(work))

    def test_numbered_title_ministerial_order(self):
        work = Work(frbr_uri='/akn/za/act/mo/2020/acsa-covid-19')
        self.assertIsNone(self.plugin.work_numbered_title(work))

    def test_numbered_title_rules(self):
        work = Work(frbr_uri='/akn/za/act/rules/2016/national-assembly')
        self.assertIsNone(self.plugin.work_numbered_title(work))
