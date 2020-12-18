# -*- coding: utf-8 -*-
import csv
import os
import pandas as pd

from django.test import testcases

from indigo.bulk_creator import BaseBulkCreator
from indigo_api.models import Country, Work
from indigo_app.models import User
from indigo_app.xlsx_exporter import *


class XLSXExporterTest(testcases.TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies']

    def setUp(self):
        self.maxDiff = None
        creator = BaseBulkCreator()
        creator.country = Country.objects.get(pk=1)
        creator.locality = None
        creator.user = User.objects.get(pk=1)
        creator.testing = True
        self.creator = creator
        self.country = Country.objects.get(pk=1)
        self.locality = None

    def import_works(self, dry_run, filename):
        file = os.path.join(os.path.dirname(__file__), filename)
        with open(file) as csv_file:
            content = csv_file.read()
            reader = csv.reader(io.StringIO(content))
            table = list(reader)
            return self.creator.create_works(table, dry_run, None)

    def write_works(self, works, filename):
        filename = os.path.join(os.path.dirname(__file__), filename)
        workbook = xlsxwriter.Workbook(filename)
        write_full_index(workbook, works)
        workbook.close()

    def write_and_compare(self, filename):
        self.import_works(False, f'{filename}.csv')
        works = Work.objects.filter(country=self.country, locality=self.locality).order_by('created_at')
        self.write_works(works, f'{filename}_output.xlsx')
        expected = os.path.join(os.path.dirname(__file__), f'{filename}_output_expected.xlsx')
        expected_content = pd.read_excel(expected, engine='openpyxl')
        output = os.path.join(os.path.dirname(__file__), f'{filename}_output.xlsx')
        output_content = pd.read_excel(output, engine='openpyxl')
        pd.testing.assert_frame_equal(expected_content, output_content)

    def test_basic(self):
        self.write_and_compare('basic')

    def test_errors(self):
        self.write_and_compare('errors')

    def test_parents(self):
        self.write_and_compare('parents')

    def test_commencements(self):
        self.write_and_compare('commencements_passive')
        self.write_and_compare('commencements_passive_later')
        # TODO: add active commencements once import is supported

    def test_amendments(self):
        self.write_and_compare('amendments_active')
        # TODO: add passive amendments once import is supported

    def test_repeals(self):
        self.write_and_compare('repeals_passive')
        # TODO: add active repeals once import is supported

    def test_duplicates(self):
        self.write_and_compare('duplicates')

    def test_taxonomies(self):
        self.write_and_compare('taxonomies')

    # TODO:
    #  - test_extra_properties (cap)
