# -*- coding: utf-8 -*-

from nose.tools import *  # noqa

from django.test import testcases
from indigo_api.importers.pl import ImporterPL


class ImporterPLTestCase(testcases.TestCase):
    def setUp(self):
        self.importer = ImporterPL()

    def test_simple_reformat(self):
        text = "something to reformat"
        reformatted = self.importer.reformat_text(text)

        assert_equal(reformatted, text)
