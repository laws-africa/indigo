import os
import unittest.util

from django.test import TestCase

from indigo_api.models import Document, Language, Work
from indigo_api.importers.base import Importer

# don't truncate diff strings
# see https://stackoverflow.com/questions/43842675/how-to-prevent-truncating-of-string-in-unit-test-python
unittest.util._MAX_LENGTH = 999999999


class XslTest(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work']
    maxDiff = None

    def setUp(self):
        self.eng = Language.objects.get(language__pk='en')
        self.work = Work.objects.get(frbr_uri='/akn/za/act/1998/2')
        self.importer = Importer()

    def run_file_test(self, prefix, update=False):
        doc = Document(title="test", language=self.eng, work=self.work)

        text = open(os.path.join(os.path.dirname(__file__), f'importer_fixtures/{prefix}.txt')).read()
        doc.document_xml = self.importer.parse_from_text(text, doc.expression_uri)
        actual = doc.to_html()

        if update:
            # update the fixture to match the actual
            open(os.path.join(os.path.dirname(__file__), f'importer_fixtures/{prefix}.html'), 'w').write(actual)
        expected = open(os.path.join(os.path.dirname(__file__), f'importer_fixtures/{prefix}.html')).read()

        self.assertMultiLineEqual(expected, actual)

    def test_footnotes(self):
        self.run_file_test("footnotes")

    def test_attribs(self):
        self.run_file_test("attribs")
