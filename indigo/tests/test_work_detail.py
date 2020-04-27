from django.test import TestCase

from indigo.analysis.work_detail import BaseWorkDetail
from indigo_api.models import Work


class BaseWorkDetailTestCase(TestCase):
    fixtures = ['languages_data', 'countries']

    def setUp(self):
        self.plugin = BaseWorkDetail()

    def test_numbered_title_simple(self):
        work = Work(frbr_uri='/za/act/1999/32')
        self.assertEqual('Act 32 of 1999', self.plugin.work_numbered_title(work))

    def test_numbered_title_caps(self):
        work = Work(frbr_uri='/za/act/gn/1999/r32')
        self.assertEqual('Government Notice R32 of 1999', self.plugin.work_numbered_title(work))

    def test_numbered_title_none(self):
        work = Work(frbr_uri='/za/act/1999/constitution')
        self.assertIsNone(self.plugin.work_numbered_title(work))

    def test_numbered_title_ignore_subtype(self):
        plugin = BaseWorkDetail()
        plugin.no_numbered_title_subtypes = ['gn']
        work = Work(frbr_uri='/za/act/gn/1999/32')
        self.assertIsNone(plugin.work_numbered_title(work))
