from nose.tools import *
from django.test import TestCase
from datetime import date

from indigo_api.models import Document
from indigo_api.tests.fixtures import *

class DocumentTestCase(TestCase):
    def setUp(self):
        pass

    def test_empty_document(self):
        d = Document()
        self.assertIsNotNone(d.doc)

    def test_change_title(self):
        d = Document.objects.create(title="Title", frbr_uri="/za/act/1980/01")
        d.save()
        id = d.id
        self.assertTrue(d.document_xml.startswith('<akomaNtoso'))

        d2 = Document.objects.get(id=id)
        self.assertEqual(d.title, d2.title)

    def test_set_content(self):
        d = Document()
        d.content = document_fixture('test')

        assert_equal(d.frbr_uri, '/za/act/1900/1')
        assert_equal(d.country, 'za')
        assert_equal(d.doc.publication_date, date(2005, 7, 24))
