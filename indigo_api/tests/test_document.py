from django.test import TestCase
from indigo_api.models import Document

class DocumentTestCase(TestCase):
    def setUp(self):
        pass

    def test_empty_document(self):
        d = Document()
        self.assertIsNotNone(d.doc)

    def test_change_title(self):
        d = Document.objects.create(title="Title", frbr_uri="/za/uri")
        d.save()
        id = d.id
        self.assertTrue(d.document_xml.startswith('<akomaNtoso'))

        d2 = Document.objects.get(id=id)
        self.assertEqual(d.title, d2.title)

    def test_set_body(self):
        d = Document.objects.create(title="Title", frbr_uri="/za/uri")
        d.body = '<body>hello</body>'
        d.save()
        id = d.id

        d2 = Document.objects.get(id=id)
        self.assertIn('<body>hello</body>', d2.document_xml)

