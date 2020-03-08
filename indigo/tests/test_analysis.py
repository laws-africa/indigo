# -*- coding: utf-8 -*-
from django.test import TestCase

from indigo.analysis.work_detail import BaseWorkDetail
from indigo_api.models import Work


class WorkDetailTestCase(TestCase):
    def setUp(self):
        self.plugin = BaseWorkDetail()

    def test_work_numbered_title_act(self):
        work = Work(frbr_uri='/na/act/2009/22', title='My Act')
        self.assertEqual(self.plugin.work_numbered_title(work), 'Act 22 of 2009')

    def test_work_numbered_title_cap(self):
        work = Work(frbr_uri='/na/act/2009/cap22', title='My Act')
        self.assertEqual(self.plugin.work_numbered_title(work), 'Chapter 22 of 2009')

    def test_work_friendly_type_cap(self):
        work = Work(frbr_uri='/na/act/2009/cap22', title='My Act')
        self.assertEqual(self.plugin.work_friendly_type(work), 'Chapter')

    def test_work_friendly_type_subtype(self):
        work = Work(frbr_uri='/na/act/by-law/2009/foo', title='My By-law')
        self.assertEqual(self.plugin.work_friendly_type(work), 'By-law')
