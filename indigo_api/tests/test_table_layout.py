import json
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase
from lxml import etree
from lxml.builder import ElementMaker

from indigo_api.exporters import PDFExporter
from indigo_api.table_layout import TableLayout


class TableLayoutTest(SimpleTestCase):
    def test_shared_layout_cases(self):
        cases = json.loads(Path(__file__).with_name('table_layout_cases.json').read_text())['cases']
        for case in cases:
            with self.subTest(case=case['name']):
                plan = TableLayout(case['rows'], case.get('columns')).plan()
                expected = case['expected']
                if expected is None:
                    self.assertIsNone(plan)
                    continue
                self.assertIsNotNone(plan)
                spans = [[] for _ in case['rows']]
                for cell in plan['cells']:
                    spans[cell['row']].append(cell['colspan'])
                self.assertEqual(expected['spans'], spans)
                self.assertEqual(len(expected['widths']), len(plan['compact_widths']))
                for actual, wanted in zip(plan['compact_widths'], expected['widths']):
                    self.assertAlmostEqual(wanted, actual)
                # Editor-save adapter stores visible cell widths, preserving
                # the same compact grid when Python reads that saved XML.
                saved_rows = [[dict(cell) for cell in row] for row in case['rows']]
                for cell in plan['cells']:
                    saved_rows[cell['row']][cell['index']].update(colspan=str(cell['colspan']), style=f'width:{cell["width"]}%')
                saved_plan = TableLayout(saved_rows).plan()
                self.assertIsNotNone(saved_plan)
                for actual, wanted in zip(saved_plan['widths'], plan['compact_widths']):
                    self.assertAlmostEqual(wanted, actual)

    def test_fop_covered_rows_are_removed_with_correct_rowspan_adjustment(self):
        ns = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0'
        maker = ElementMaker(namespace=ns, nsmap={None: ns})
        table = etree.XML(f'<table xmlns="{ns}"><tr><td rowspan="3"><p>A</p></td>'
                          '<td rowspan="2"><p>B</p></td></tr><tr/><tr><td><p>C</p></td></tr></table>')
        doc = SimpleNamespace(root=maker.mainBody(table), namespace=ns, maker=maker)
        PDFExporter().resize_tables(doc)
        self.assertEqual(['2', '1'], table.xpath('a:tr[1]/a:td/@rowspan', namespaces={'a': ns}))
        self.assertEqual(2, len(table.findall(f'{{{ns}}}tr')))
        self.assertEqual(['A', 'B', 'C'], table.xpath('a:tr/a:td/a:p/text()', namespaces={'a': ns}))

    def test_combined_rowspan_uses_actual_column_for_width(self):
        ns = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0'
        maker = ElementMaker(namespace=ns, nsmap={None: ns})
        table = etree.XML(f'<table xmlns="{ns}"><tr><td colspan="2" rowspan="2" style="width:80%"><p>A</p></td>'
                          '<td style="width:20%"><p>B</p></td></tr><tr><td style="width:20%"><p>C</p></td></tr>'
                          '<tr><td style="width:30%"><p>D</p></td><td style="width:50%"><p>E</p></td><td style="width:20%"><p>F</p></td></tr></table>')
        PDFExporter().resize_tables(SimpleNamespace(root=maker.mainBody(table), namespace=ns, maker=maker))
        self.assertEqual([30, 50, 20], [float(c.get('width')[:-1]) for c in table.findall(f'{{{ns}}}colgroup/{{{ns}}}col')])

    def test_dense_legacy_mapper_enforces_grid_limits(self):
        ns = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0'
        maker = ElementMaker(namespace=ns, nsmap={None: ns})
        table = etree.XML(f'<table xmlns="{ns}"><tr><td colspan="10000"/><td colspan="10000"/></tr></table>')
        with self.assertRaisesMessage(ValueError, 'Table exceeds supported grid size'):
            PDFExporter().resize_tables(SimpleNamespace(root=maker.mainBody(table), namespace=ns, maker=maker))
