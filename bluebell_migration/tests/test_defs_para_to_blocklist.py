from lxml import etree
import os

from django.test import TestCase

from bluebell_migration.migrate import SlawToBluebell, IdGenerator


class DefsParaToBlocklistTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.id_generator = IdGenerator()

    def run_it(self, fname):
        migration = SlawToBluebell()

        old = os.path.join(os.path.dirname(__file__), 'definitions_fixtures', f'{fname}.xml')
        with open(old, 'r') as old:
            old = old.read()
        xml = etree.fromstring(old)

        new = os.path.join(os.path.dirname(__file__), 'definitions_fixtures', f'{fname}_after.xml')
        with open(new, 'r') as new:
            new = new.read()

        _, xml = migration.migrate_xml(xml)

        xml = etree.tostring(xml, encoding='unicode')
        xml = etree.tostring(etree.fromstring(migration.unpretty(xml)), pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual(new, xml)

    def test_basic(self):
        self.run_it('basic')

    def test_nested(self):
        self.run_it('nested')

    def test_nested_extra(self):
        self.run_it('nested_xtra')

    def test_legit_hier(self):
        self.run_it('legit_hier')

    def test_subsections(self):
        self.run_it('subsections')

    def test_legit_hier_with_subsections(self):
        self.run_it('legit_hier_with_subsections')
