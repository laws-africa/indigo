import os
import tempfile
from lxml import etree

from django.test import TestCase

from cobalt.hierarchical import Act
from indigo_api.exporters import PDFExporter
from indigo_api.pdf import run_fop
from indigo_api.models import Document, Work, Language


class PDFExporterTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work']
    maxDiff = None
    # show diffs, no matter how big
    _diffThreshold = 999999999

    def setUp(self):
        self.exporter = PDFExporter()
        self.maxDiff = None
        self.eng = Language.objects.get(language__pk='en')
        self.work = Work.objects.get(frbr_uri='/akn/za/act/1998/2')
        self.document = Document(title="test", language=self.eng, work=self.work)
        self.xsl_fo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'xsl', 'fo', 'fo_akn.xsl')

    def run_and_compare(self, name, update=False):
        input_path = os.path.join(os.path.dirname(__file__), 'pdf_fixtures', f'{name}_in.xml')
        output_path = os.path.join(os.path.dirname(__file__), 'pdf_fixtures', f'{name}_out.xml')

        with open(input_path, 'r') as f:
            xml_in = f.read()

        # run fop
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_file = os.path.join(tmpdir, 'raw.xml')
            with open(xml_file, "wb") as f:
                f.write(xml_in.encode('utf-8'))
            outf = tempfile.NamedTemporaryFile('rb', dir=tmpdir, suffix='.xml')
            xsl_fo = self.xsl_fo_path
            self.exporter.update_base_xsl_fo_dir(xsl_fo)
            run_fop(outf.name, tmpdir, xml_file, xsl_fo, output_fo=True)
            pretty_xml_out = etree.tostring(etree.fromstring(outf.read()), pretty_print=True, encoding='unicode')

            if update:
                # update the fixture to match the actual
                with open(output_path, 'w') as ff:
                    ff.write(pretty_xml_out)

        with open(output_path, 'r') as f:
            expected = f.read()

        self.assertMultiLineEqual(expected, pretty_xml_out)

    def adjust_xml(self, name, adjustment, update=False):
        input_path = os.path.join(os.path.dirname(__file__), 'pdf_fixtures', f'{name}_in.xml')
        output_path = os.path.join(os.path.dirname(__file__), 'pdf_fixtures', f'{name}_out.xml')

        with open(input_path, 'r') as f:
            xml_in = f.read()

        # do the adjustment
        doc = Act(xml=xml_in)
        adjustment(doc)

        xml_out = etree.tostring(doc.root, encoding='unicode', pretty_print=True)
        if update:
            # update the fixture to match the actual
            with open(output_path, 'w') as f:
                f.write(xml_out)

        with open(output_path, 'r') as f:
            expected = f.read()

        self.assertMultiLineEqual(expected, xml_out)

    def test_basic(self):
        self.run_and_compare('basic')

    def test_adjust_refs(self):
        self.adjust_xml('links', self.exporter.adjust_refs)
