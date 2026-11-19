from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase
from lxml import etree
from lxml.builder import ElementMaker

from indigo_api.exporters import PDFExporter


class ExplicitFormattingTestCase(SimpleTestCase):
    namespace = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0'
    ns = {'a': namespace, 'f': 'http://www.w3.org/1999/XSL/Format'}

    def transform(self, content):
        core = Path(PDFExporter.base_xsl_fo_dir)
        imports = ''.join(f'<xsl:import href="{(core / name).as_uri()}"/>' for name in
                          ['_variables.xsl', '_formatting.xsl', '_blocks.xsl', '_tables.xsl'])
        xsl = etree.XML(f'''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
          {imports}<xsl:variable name="fontsize">10pt</xsl:variable>
          <xsl:template match="/"><root><xsl:apply-templates/></root></xsl:template>
        </xsl:stylesheet>''')
        return etree.XSLT(xsl)(etree.XML(f'<mainBody xmlns="{self.namespace}">{content}</mainBody>'))

    def test_explicit_tiers_and_descendant_override(self):
        for tier, expected in [('normal', '10pt'), ('small', '8pt'), ('xsmall', '7pt'), ('xxsmall', '6pt')]:
            fo = self.transform(f'<table class="custom akn--text-{tier}"><tr>'
                                f'<td><p class="akn--text-{tier}">Same tier</p></td>'
                                '<td class="akn--text-normal"><p>Normal</p></td></tr></table>')
            self.assertEqual(expected, fo.xpath('//f:table/@font-size', namespaces=self.ns)[0])
            blocks = fo.xpath('//f:table-cell/f:block', namespaces=self.ns)
            self.assertEqual(expected, blocks[0][0].get('font-size'))
            self.assertEqual('10pt', blocks[1].get('font-size'))

    def test_alignment_inheritance_and_defaults(self):
        for value, expected in [('left', 'start'), ('center', 'center'), ('right', 'end'), ('justify', 'justify')]:
            fo = self.transform(f'<table class="custom akn--text-{value}"><tr>'
                                '<td><p>Inherited</p></td><td class="akn--text-right">'
                                '<p class="akn--text-left">Override</p></td></tr></table>')
            blocks = fo.xpath('//f:table-cell/f:block', namespaces=self.ns)
            self.assertEqual(expected, blocks[0].get('text-align'))
            self.assertEqual('end', blocks[1].get('text-align'))
            self.assertEqual('start', blocks[1][0].get('text-align'))
        fo = self.transform('<table><tr><td><p>Default</p></td><th><p>Heading</p></th></tr></table>')
        self.assertEqual(['start', 'center'], fo.xpath('//f:table-cell/f:block/@text-align', namespaces=self.ns))
        self.assertFalse(fo.xpath('//f:table/@font-size', namespaces=self.ns))

    def test_padding_and_class_token_matching(self):
        fo = self.transform('<table class="custom akn--no-padding"><tr><td><p>Text</p></td></tr></table>')
        self.assertEqual('0pt', fo.xpath('//f:table-cell/@padding-left', namespaces=self.ns)[0])
        fo = self.transform('<table class="akn--text-right-other akn--no-padding-other"><tr><td><p>Text</p></td></tr></table>')
        self.assertEqual('start', fo.xpath('//f:table-cell/f:block/@text-align', namespaces=self.ns)[0])
        self.assertFalse(fo.xpath('//f:table-cell/@padding-left', namespaces=self.ns))

    def test_preprocessing_preserves_authored_classes_and_border(self):
        maker = ElementMaker(namespace=self.namespace, nsmap={None: self.namespace})
        table = maker.table(maker.tr(*[maker.td(maker.p('Text')) for _ in range(6)]),
                            **{'class': 'custom akn--text-small akn--text-justify'})
        doc = SimpleNamespace(root=maker.mainBody(table), namespace=self.namespace, maker=maker)
        PDFExporter().resize_tables(doc)
        self.assertEqual({'custom', 'akn--text-small', 'akn--text-justify', 'border'}, set(table.get('class').split()))
        self.assertNotIn('akn--text-xsmall', table.get('class'))

    def test_html_preserves_classes_without_exposing_legacy_fontsize(self):
        stylesheet = Path(PDFExporter.base_xsl_fo_dir).parent / 'html_akn.xsl'
        html = etree.XSLT(etree.parse(str(stylesheet)))(etree.XML(
            f'<table xmlns="{self.namespace}" fontsize="9" class="akn--text-small"><tr><td><p class="akn--text-left">Text</p></td></tr></table>'))
        self.assertFalse(html.xpath('//table/@fontsize'))
        self.assertIn('akn--text-small', html.xpath('//table/@class')[0])
        self.assertIn('akn--text-left', html.xpath('//span/@class')[0])

    def test_preprocessing_and_standard_entry_support_all_alignment_classes(self):
        maker = ElementMaker(namespace=self.namespace, nsmap={None: self.namespace})
        exporter = PDFExporter()
        entry = Path(exporter.base_xsl_fo_dir) / 'fo_akn.xsl'
        transform = etree.XSLT(etree.XML(exporter.update_base_xsl_fo_dir(str(entry)).encode(), base_url=entry.as_uri()))
        for alignment, expected in [('left', 'start'), ('center', 'center'), ('right', 'end'), ('justify', 'justify')]:
            with self.subTest(alignment=alignment):
                cell = maker.td(maker.p('Inherited'), maker.p('Paragraph override', **{'class': 'akn--text-right'}),
                                **{'class': f'custom akn--text-{alignment} akn--text-small'})
                table = maker.table(maker.tr(cell), **{'class': 'akn--text-center akn--text-normal'})
                doc = SimpleNamespace(root=maker.akomaNtoso(maker.act(maker.body(table))), namespace=self.namespace, maker=maker)
                exporter.resize_tables(doc)
                self.assertEqual(alignment, cell.get('style'))
                fo = transform(doc.root)
                blocks = fo.xpath('//f:table-cell/f:block', namespaces=self.ns)
                self.assertEqual(expected, blocks[0].get('text-align'))
                self.assertEqual('8pt', blocks[0].get('font-size'))
                self.assertEqual('end', blocks[0][1].get('text-align'))
                self.assertEqual('9pt', fo.xpath('//f:table/@font-size', namespaces=self.ns)[0])

    def test_preprocessing_alignment_matches_whole_tokens(self):
        maker = ElementMaker(namespace=self.namespace, nsmap={None: self.namespace})
        cell = maker.td(maker.p('Text'), **{'class': 'akn--text-justify-other akn--text-leftover'})
        doc = SimpleNamespace(root=maker.mainBody(maker.table(maker.tr(cell))), namespace=self.namespace, maker=maker)
        PDFExporter().resize_tables(doc)
        self.assertIsNone(cell.get('style'))
