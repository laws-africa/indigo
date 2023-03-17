from lxml import etree
import os

from django.test import TestCase

from bluebell.xml import IdGenerator
from bluebell_migration.migrate import BlocklistToPara, pretty_c14n, SlawToBluebell


class BlocklistToParaTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None

    def run_it(self, fname, unwrapped=False, fin=False):
        """ Don't pass both unwrapped and fin as True"""
        migration = BlocklistToPara()
        new_name = 'hier'
        if fin:
            new_name = 'fin'
        elif unwrapped:
            new_name = 'unwrapped'

        old = os.path.join(os.path.dirname(__file__), 'fixtures', f'{fname}_bl.xml')
        with open(old, 'r') as old:
            old = old.read()
        xml = etree.fromstring(old)

        new = os.path.join(os.path.dirname(__file__), 'fixtures', f'{fname}_{new_name}.xml')
        with open(new, 'r') as new:
            new = new.read()

        migration.blocklist_to_para(xml)

        if unwrapped:
            migration.unwrap_hcontainers(xml)
        elif fin:
            migration.unwrap_hcontainers(xml)
            migration.intro_and_wrapup(xml)
        IdGenerator().rewrite_all_eids(xml)

        xml = etree.tostring(xml, encoding='unicode')
        xml = pretty_c14n(SlawToBluebell().unpretty(xml))
        self.assertMultiLineEqual(new, xml)

    def test_basic(self):
        self.run_it('basic')

    def test_basic_unwrapped(self):
        self.run_it('basic', unwrapped=True)

    def test_basic_fin(self):
        self.run_it('basic', fin=True)

    def test_crossheading1(self):
        """ crossHeadings at every possible level between each element"""
        self.run_it('crossheading1')

    def test_crossheading1_unwrapped(self):
        self.run_it('crossheading1', unwrapped=True)

    def test_crossheading1_fin(self):
        self.run_it('crossheading1', fin=True)

    def test_crossheading2(self):
        """ crossHeadings at every possible level between each element"""
        self.run_it('crossheading2')

    def test_crossheading2_unwrapped(self):
        self.run_it('crossheading2', unwrapped=True)

    def test_crossheading2_fin(self):
        self.run_it('crossheading2', fin=True)

    def test_edge_listintro(self):
        self.run_it('edge_listintro')

    def test_edge_listintro_unwrapped(self):
        self.run_it('edge_listintro', unwrapped=True)

    def test_edge_listintro_fin(self):
        self.run_it('edge_listintro', fin=True)

    def test_intervening(self):
        self.run_it('intervening')

    def test_intervening_unwrapped(self):
        self.run_it('intervening', unwrapped=True)

    def test_intervening_fin(self):
        self.run_it('intervening', fin=True)

    def test_intro(self):
        self.run_it('intro')

    def test_intro_unwrapped(self):
        self.run_it('intro', unwrapped=True)

    def test_intro_fin(self):
        self.run_it('intro', fin=True)

    def test_intro_wrap(self):
        self.run_it('intro_wrap')

    def test_intro_wrap_unwrapped(self):
        self.run_it('intro_wrap', unwrapped=True)

    def test_intro_wrap_fin(self):
        self.run_it('intro_wrap', fin=True)

    def test_listintro(self):
        self.run_it('listintro')

    def test_listintro_unwrapped(self):
        self.run_it('listintro', unwrapped=True)

    def test_listintro_fin(self):
        self.run_it('listintro', fin=True)

    def test_listwrapup(self):
        self.run_it('listwrapup')

    def test_listwrapup_unwrapped(self):
        self.run_it('listwrapup', unwrapped=True)

    def test_listwrapup_fin(self):
        self.run_it('listwrapup', fin=True)

    def test_siblings(self):
        self.run_it('siblings')

    def test_siblings_unwrapped(self):
        self.run_it('siblings', unwrapped=True)

    def test_siblings_fin(self):
        self.run_it('siblings', fin=True)

    def test_subparagraphs(self):
        self.run_it('subparagraphs')

    def test_subparagraphs_unwrapped(self):
        self.run_it('subparagraphs', unwrapped=True)

    def test_subparagraphs_fin(self):
        self.run_it('subparagraphs', fin=True)

    def test_top_level(self):
        self.run_it('top_level')

    def test_top_level_unwrapped(self):
        self.run_it('top_level', unwrapped=True)

    def test_top_level_fin(self):
        self.run_it('top_level', fin=True)

    def test_wrap(self):
        self.run_it('wrap')

    def test_wrap_unwrapped(self):
        self.run_it('wrap', unwrapped=True)

    def test_wrap_fin(self):
        self.run_it('wrap', fin=True)
