from django.test import TestCase
from indigo_api.models import Document

class DocumentTestCase(TestCase):
    def setUp(self):
        Document.objects.create()

    def test_empty_document(self):
        d = Document()
        self.assertIsNotNone(d.doc)
