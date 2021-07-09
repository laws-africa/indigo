# -*- coding: utf-8 -*-
from copy import deepcopy
from dotmap import DotMap
from django.test import TestCase

from indigo.analysis.toc.base import TOCElement, TOCBuilderBase, CommencementsBeautifier, descend_toc_pre_order


class BeautifulProvisionsTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.beautifier = CommencementsBeautifier()
        self.commenceable_provisions = self.make_toc_elements('section-', 'section', range(1, 31), basic_unit=True)
        self.toc_plugin = TOCBuilderBase()

        items_3 = self.make_toc_elements('sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_', 'item', ['A', 'B'])
        items_2 = self.make_toc_elements('sec_1__subsec_1__list_1__item_a__list_1__item_', 'item', ['i', 'ii', 'iii'])
        items_2[1].children = items_3
        items_1 = self.make_toc_elements('sec_1__subsec_1__list_1__item_', 'item', ['a', 'aA', 'b', 'c'])
        items_1[0].children = items_2
        subsections = self.make_toc_elements('sec_1__subsec_', 'subsection', range(1, 5))
        subsections[0].children = items_1
        sections = self.make_toc_elements('sec_', 'section', range(1, 8), basic_unit=True)
        sections[0].children = subsections
        parts = self.make_toc_elements('chp_1__part_', 'part', ['A', 'B'], with_brackets=False)
        parts[0].children = sections[:3]
        parts[1].children = sections[3:5]
        chapters = self.make_toc_elements('chp_', 'chapter', ['1', '2'], with_brackets=False)
        chapters[0].children = parts
        chapters[1].children = sections[5:]

        self.chapters = chapters

    def make_toc_elements(self, prefix, type, list_of_nums, basic_unit=False, with_brackets=True):
        def get_num(n):
            if basic_unit:
                return f'{n}.'
            elif with_brackets:
                return f'({n})'
            return n

        return [TOCElement(
            element=None, component=None, children=[], type_=type,
            id_=f'{prefix}{n}',
            num=get_num(n), basic_unit=basic_unit
        ) for n in list_of_nums]

    def test_beautiful_provisions_basic(self):
        provision_ids = ['section-1', 'section-2', 'section-3', 'section-4']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 1–4')

        provision_ids = ['section-2', 'section-3', 'section-4', 'section-5']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 2–5')

        provision_ids = ['section-1', 'section-2', 'section-3']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 1–3')

        provision_ids = ['section-1', 'section-3', 'section-4', 'section-5', 'section-6']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 1; section 3–6')

        provision_ids = ['section-1', 'section-2', 'section-3', 'section-4', 'section-5', 'section-7']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 1–5; section 7')

        provision_ids = ['section-1', 'section-3', 'section-4', 'section-5', 'section-6', 'section-8']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 1; section 3–6; section 8')

        provision_ids = ['section-1', 'section-4', 'section-5', 'section-6', 'section-7', 'section-8', 'section-9', 'section-10', 'section-11', 'section-12', 'section-14', 'section-16', 'section-20', 'section-21']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 1; section 4–12; section 14; section 16; section 20–21')

    def test_one_item(self):
        provision_ids = ['section-23']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 23')

    def test_two_items(self):
        provision_ids = ['section-23', 'section-25']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 23; section 25')

    def test_three_items(self):
        provision_ids = ['section-23', 'section-24', 'section-25']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 23–25')

    def test_one_excluded(self):
        commenceable_provisions = self.make_toc_elements('section-', 'section', range(1, 4), basic_unit=True)

        provision_ids = ['section-1', 'section-2']
        description = self.beautifier.make_beautiful(commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 1–2')

        provision_ids = ['section-2', 'section-3']
        description = self.beautifier.make_beautiful(commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 2–3')

    def run_nested(self, provision_ids):
        nested_toc = deepcopy(self.chapters)
        return self.beautifier.make_beautiful(nested_toc, provision_ids)

    def test_nested_full_containers(self):
        # Don't dig down further than what is fully commenced
        provision_ids = [
            'chp_1', 'chp_1__part_A', 'sec_1', 'sec_1__subsec_1',
            'sec_1__subsec_1__list_1__item_a',
            'sec_1__subsec_1__list_1__item_a__list_1__item_i',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_A',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_B',
            'sec_1__subsec_1__list_1__item_a__list_1__item_iii',
            'sec_1__subsec_1__list_1__item_aA',
            'sec_1__subsec_1__list_1__item_b',
            'sec_1__subsec_1__list_1__item_c',
            'sec_1__subsec_2', 'sec_1__subsec_3', 'sec_1__subsec_4',
            'sec_2', 'sec_3',
            'chp_1__part_B', 'sec_4', 'sec_5',
            'chp_2', 'sec_6', 'sec_7',
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (section 1–5); Chapter 2 (section 6–7)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (section 1–5); Chapter 2 (section 6–7)', self.run_nested(provision_ids))

        provision_ids = [
            'chp_1', 'chp_1__part_A',
            'sec_1', 'sec_1__subsec_1',
            'sec_1__subsec_1__list_1__item_a',
            'sec_1__subsec_1__list_1__item_a__list_1__item_i',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_A',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_B',
            'sec_1__subsec_1__list_1__item_a__list_1__item_iii',
            'sec_1__subsec_1__list_1__item_aA',
            'sec_1__subsec_1__list_1__item_b',
            'sec_1__subsec_1__list_1__item_c',
            'sec_1__subsec_2', 'sec_1__subsec_3', 'sec_1__subsec_4',
            'sec_2', 'sec_3',
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (section 1–3)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (section 1–3)', self.run_nested(provision_ids))

        # don't repeat 'Chapter 1' before Part B
        provision_ids = [
            'sec_2', 'sec_3',
            'chp_1__part_B', 'sec_4', 'sec_5',
            'chp_2', 'sec_6', 'sec_7'
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A, section 2–3; Part B (section 4–5); Chapter 2 (section 6–7)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A, section 2–3; Part B (section 4–5); Chapter 2 (section 6–7)', self.run_nested(provision_ids))

    def test_nested_partial_containers(self):
        # Chapter 1 is mentioned regardless because it's given
        provision_ids = ['chp_1', 'sec_2']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A, section 2', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A, section 2', self.run_nested(provision_ids))

        # Chapter 1, Part B are mentioned regardless because they're given
        provision_ids = [
            'chp_1', 'chp_1__part_A',
            'sec_1', 'sec_1__subsec_1',
            'sec_1__subsec_1__list_1__item_a',
            'sec_1__subsec_1__list_1__item_a__list_1__item_i',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_A',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_B',
            'sec_1__subsec_1__list_1__item_a__list_1__item_iii',
            'sec_1__subsec_1__list_1__item_aA',
            'sec_1__subsec_1__list_1__item_b',
            'sec_1__subsec_1__list_1__item_c',
            'sec_1__subsec_2', 'sec_1__subsec_3', 'sec_1__subsec_4',
            'sec_2', 'sec_3',
            'chp_1__part_B',
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (section 1–3); Part B (in part)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (section 1–3); Part B (in part)', self.run_nested(provision_ids))

        provision_ids = [
            'chp_1', 'chp_1__part_A',
            'sec_1', 'sec_1__subsec_1',
            'sec_1__subsec_1__list_1__item_a',
            'sec_1__subsec_1__list_1__item_a__list_1__item_i',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_A',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_B',
            'sec_1__subsec_1__list_1__item_a__list_1__item_iii',
            'sec_1__subsec_1__list_1__item_aA',
            'sec_1__subsec_1__list_1__item_b',
            'sec_1__subsec_1__list_1__item_c',
            'sec_1__subsec_2', 'sec_1__subsec_3', 'sec_1__subsec_4',
            'sec_2', 'sec_3',
            'chp_1__part_B', 'sec_4',
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (section 1–3); Part B (in part); Part B, section 4', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (section 1–3); Part B (in part); Part B, section 4', self.run_nested(provision_ids))

        # Chapter 1, Part A is mentioned (even though it's not given) for context
        provision_ids = ['chp_1', 'sec_2', 'chp_1__part_B']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A, section 2; Part B (in part)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A, section 2; Part B (in part)', self.run_nested(provision_ids))

        provision_ids = ['sec_2', 'chp_1__part_B']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A, section 2; Part B (in part)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A, section 2; Part B (in part)', self.run_nested(provision_ids))

        provision_ids = [
            'chp_1__part_A',
            'sec_1', 'sec_1__subsec_1',
            'sec_1__subsec_1__list_1__item_a',
            'sec_1__subsec_1__list_1__item_a__list_1__item_i',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_A',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_B',
            'sec_1__subsec_1__list_1__item_a__list_1__item_iii',
            'sec_1__subsec_1__list_1__item_aA',
            'sec_1__subsec_1__list_1__item_b',
            'sec_1__subsec_1__list_1__item_c',
            'sec_1__subsec_2', 'sec_1__subsec_3', 'sec_1__subsec_4',
            'sec_2', 'sec_3', 'sec_4',
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A (section 1–3); Part B, section 4', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A (section 1–3); Part B, section 4', self.run_nested(provision_ids))

        # Part B isn't given in full even though all its basic units have commenced because it's not mentioned 
        # Both Part A and Part B are given for context 
        provision_ids = ['chp_1', 'sec_2', 'sec_4', 'sec_5']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A, section 2; Part B, section 4–5', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A, section 2; Part B, section 4–5', self.run_nested(provision_ids))

        provision_ids = [
            'chp_1__part_A',
            'sec_1', 'sec_1__subsec_1',
            'sec_1__subsec_1__list_1__item_a',
            'sec_1__subsec_1__list_1__item_a__list_1__item_i',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_A',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_B',
            'sec_1__subsec_1__list_1__item_a__list_1__item_iii',
            'sec_1__subsec_1__list_1__item_aA',
            'sec_1__subsec_1__list_1__item_b',
            'sec_1__subsec_1__list_1__item_c',
            'sec_1__subsec_2', 'sec_1__subsec_3', 'sec_1__subsec_4',
            'sec_2', 'sec_3', 'sec_4', 'sec_5',
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A (section 1–3); Part B, section 4–5', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A (section 1–3); Part B, section 4–5', self.run_nested(provision_ids))

        provision_ids = ['chp_1', 'sec_2', 'chp_1__part_B', 'sec_4', 'sec_5']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A, section 2; Part B (section 4–5)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A, section 2; Part B (section 4–5)', self.run_nested(provision_ids))

        provision_ids = ['chp_1__part_B']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part B (in part)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part B (in part)', self.run_nested(provision_ids))

    def test_nested_basic_units(self):
        provision_ids = [
            'sec_2', 'sec_3',
            'chp_1__part_B', 'sec_5',
            'chp_2', 'sec_7'
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A, section 2–3; Part B (in part); Part B, section 5; Chapter 2 (in part); Chapter 2, section 7', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A, section 2–3; Part B (in part); Part B, section 5; Chapter 2 (in part); Chapter 2, section 7', self.run_nested(provision_ids))

        provision_ids = [
            'sec_2', 'sec_3',
            'sec_5',
            'sec_7'
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A, section 2–3; Part B, section 5; Chapter 2, section 7', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A, section 2–3; Part B, section 5; Chapter 2, section 7', self.run_nested(provision_ids))

        provision_ids = ['sec_4', 'chp_2', 'sec_6']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part B, section 4; Chapter 2 (in part); Chapter 2, section 6', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part B, section 4; Chapter 2 (in part); Chapter 2, section 6', self.run_nested(provision_ids))

        provision_ids = ['sec_4', 'chp_2']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part B, section 4; Chapter 2 (in part)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part B, section 4; Chapter 2 (in part)', self.run_nested(provision_ids))

    def test_nested_single_subprovisions(self):
        provision_ids = ['sec_1__subsec_3']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A, section 1(3)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A, section 1(3)', self.run_nested(provision_ids))

        provision_ids = ['sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_A']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A, section 1(1)(a)(ii)(A)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A, section 1(1)(a)(ii)(A)', self.run_nested(provision_ids))

    def test_nested_multiple_subprovisions(self):
        # Subprovisions are listed separately with their parent context (up to basic unit) prepended.
        # Note 1(1)(a)(ii)(A) and (B) aren't commenced. They'll be listed separatey under 'uncommenced'.
        provision_ids = [
            'sec_1__subsec_1__list_1__item_a__list_1__item_i',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii',
            'sec_1__subsec_1__list_1__item_b', 'sec_1__subsec_1__list_1__item_c'
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A, section 1(1)(a)(i), 1(1)(a)(ii), 1(1)(b), 1(1)(c)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A, section 1(1)(a)(i), 1(1)(a)(ii), 1(1)(b), 1(1)(c)', self.run_nested(provision_ids))

        provision_ids = [
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_A',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii__list_1__item_B',
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A, section 1(1)(a)(ii)(A), 1(1)(a)(ii)(B)', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A, section 1(1)(a)(ii)(A), 1(1)(a)(ii)(B)', self.run_nested(provision_ids))

        # If a basic unit isn't fully commenced, don't end up with section 1(1)(a), 1(1)(c), 1(2), 1(3)–2
        provision_ids = [
            'chp_1',
            'chp_1__part_A',
            'sec_1',
            'sec_1__subsec_1',
            'sec_1__subsec_1__list_1__item_a',
            'sec_1__subsec_1__list_1__item_a__list_1__item_i',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii',
            'sec_1__subsec_1__list_1__item_a__list_1__item_iii',
            'sec_1__subsec_1__list_1__item_c',
            'sec_1__subsec_2',
            'sec_1__subsec_3',
            'sec_3'
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (in part); Part A, section 1(1)(a)(i), 1(1)(a)(ii), 1(1)(a)(iii), 1(1)(c), 1(2), 1(3); section 3', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (in part); Part A, section 1(1)(a)(i), 1(1)(a)(ii), 1(1)(a)(iii), 1(1)(c), 1(2), 1(3); section 3', self.run_nested(provision_ids))

        provision_ids = [
            'chp_1',
            'chp_1__part_A',
            'sec_1',
            'sec_1__subsec_1',
            'sec_1__subsec_1__list_1__item_a',
            'sec_1__subsec_1__list_1__item_a__list_1__item_i',
            'sec_1__subsec_1__list_1__item_a__list_1__item_ii',
            'sec_1__subsec_1__list_1__item_a__list_1__item_iii',
            'sec_1__subsec_1__list_1__item_c',
            'sec_1__subsec_2',
            'sec_1__subsec_3',
            'sec_2'
        ]
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (in part); Part A, section 1(1)(a)(i), 1(1)(a)(ii), 1(1)(a)(iii), 1(1)(c), 1(2), 1(3); section 2', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1 (in part); Chapter 1, Part A (in part); Part A, section 1(1)(a)(i), 1(1)(a)(ii), 1(1)(a)(iii), 1(1)(c), 1(2), 1(3); section 2', self.run_nested(provision_ids))

        provision_ids = ['sec_1__subsec_1__list_1__item_b', 'sec_4']
        self.beautifier.commenced = True
        self.assertEqual('Chapter 1, Part A, section 1(1)(b); Part B, section 4', self.run_nested(provision_ids))
        self.beautifier.commenced = False
        self.assertEqual('Chapter 1, Part A, section 1(1)(b); Part B, section 4', self.run_nested(provision_ids))

    def run_lonely(self, provision_ids):
        lonely_item = self.make_toc_elements('item_', 'item', ['xxx'])[0]

        nested_toc = deepcopy(self.chapters)
        nested_toc.insert(0, lonely_item)
        return self.beautifier.make_beautiful(nested_toc, provision_ids)

    def test_lonely_subprovisions(self):
        provision_ids = [
            'item_xxx',
        ]

        self.beautifier.commenced = True
        self.assertEqual('item (xxx)', self.run_lonely(provision_ids))

        self.beautifier.commenced = False
        self.assertEqual('item (xxx)', self.run_lonely(provision_ids))

    def test_provisions_out_of_sync(self):
        provision_ids = ['section-29', 'section-30', 'section-31', 'section-32']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, 'section 29–30')

        provision_ids = ['section-31', 'section-32', 'section-33', 'section-34']
        description = self.beautifier.make_beautiful(self.commenceable_provisions, provision_ids)
        self.assertEqual(description, '')

    def test_inserted(self):
        pit_1_provisions = ['1', '2', '3']
        pit_2_provisions = ['1', '1A', '2', '2A', '3', '3A']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provision_ids = [p.id for p in provisions]
        self.assertEqual(provision_ids, [
            'section-1',
            'section-1A',
            'section-2',
            'section-2A',
            'section-3',
            'section-3A',
        ])

    def run_test_insert_nested(self, list_of_lists):
        provisions = []
        id_set = set()
        for tocelement in list_of_lists:
            self.toc_plugin.insert_provisions(provisions, id_set, tocelement)
        return [p.id for p in descend_toc_pre_order(provisions)]

    def test_insert_provisions_nested(self):
        original_subsection_1_items = self.make_toc_elements('subsec_1__list_1__item_', 'item', ['a', 'b'])
        original_subsection_2_items = self.make_toc_elements('subsec_2__list_1__item_', 'item', ['a', 'b'])
        original_subsection_3_items = self.make_toc_elements('subsec_3__list_1__item_', 'item', ['a', 'b'])
        original_subsections = self.make_toc_elements('subsec_', 'subsection', ['1', '2', '3'])
        original_subsections[0].children = original_subsection_1_items
        original_subsections[1].children = original_subsection_2_items
        original_subsections[2].children = original_subsection_3_items

        inserted_subsection_1_items = self.make_toc_elements('subsec_1__list_1__item_', 'item', ['a', 'aA', 'b'])
        inserted_subsection_1a_a_subitems = self.make_toc_elements('subsec_1A__list_1__item_a__list_1__item_', 'item', ['i', 'ii'])
        inserted_subsection_1a_items = self.make_toc_elements('subsec_1A__list_1__item_', 'item', ['a', 'b'])
        inserted_subsection_1a_items[0].children = inserted_subsection_1a_a_subitems
        inserted_subsection_2_b_subitems = self.make_toc_elements('subsec_2__list_1__item_b__list_1__item_', 'item', ['A', 'B'])
        inserted_subsection_2_items = self.make_toc_elements('subsec_2__list_1__item_', 'item', ['a', 'b', 'c'])
        inserted_subsection_2_items[1].children = inserted_subsection_2_b_subitems
        inserted_subsections = self.make_toc_elements('subsec_', 'subsection', ['1', '1A', '2', '3'])
        inserted_subsections[0].children = inserted_subsection_1_items
        inserted_subsections[1].children = inserted_subsection_1a_items
        inserted_subsections[2].children = inserted_subsection_2_items
        inserted_subsections[3].children = original_subsection_3_items

        self.assertEqual([
            'subsec_1',
            'subsec_1__list_1__item_a',
            'subsec_1__list_1__item_aA',
            'subsec_1__list_1__item_b',
            'subsec_1A',
            'subsec_1A__list_1__item_a',
            'subsec_1A__list_1__item_a__list_1__item_i',
            'subsec_1A__list_1__item_a__list_1__item_ii',
            'subsec_1A__list_1__item_b',
            'subsec_2',
            'subsec_2__list_1__item_a',
            'subsec_2__list_1__item_b',
            'subsec_2__list_1__item_b__list_1__item_A',
            'subsec_2__list_1__item_b__list_1__item_B',
            'subsec_2__list_1__item_c',
            'subsec_3',
            'subsec_3__list_1__item_a',
            'subsec_3__list_1__item_b',
        ], self.run_test_insert_nested([deepcopy(original_subsections), deepcopy(inserted_subsections)]))

        removed_subsection_1_items = self.make_toc_elements('subsec_1__list_1__item_', 'item', ['b'])
        removed_subsections = self.make_toc_elements('subsec_', 'subsection', ['1', '3'])
        removed_subsections[0].children = removed_subsection_1_items
        removed_subsections[1].children = original_subsection_3_items

        self.assertEqual([
            'subsec_1',
            'subsec_1__list_1__item_a',
            'subsec_1__list_1__item_b',
            'subsec_2',
            'subsec_2__list_1__item_a',
            'subsec_2__list_1__item_b',
            'subsec_3',
            'subsec_3__list_1__item_a',
            'subsec_3__list_1__item_b',
        ], self.run_test_insert_nested([deepcopy(original_subsections), deepcopy(removed_subsections)]))

        changed_subsection_1_aa_subitems = self.make_toc_elements('subsec_1__list_1__item_aA__list_1__item_', 'item', ['i', 'ii'])
        changed_subsection_1_items = self.make_toc_elements('subsec_1__list_1__item_', 'item', ['aA', 'b'])
        changed_subsection_1_items[0].children = changed_subsection_1_aa_subitems
        changed_subsection_1a_items = self.make_toc_elements('subsec_1A__list_1__item_', 'item', ['a', 'b'])
        changed_subsection_3_items = self.make_toc_elements('subsec_3__list_1__item_', 'item', ['c'])
        changed_subsections = self.make_toc_elements('subsec_', 'subsection', ['1', '1A', '3'])
        changed_subsections[0].children = changed_subsection_1_items
        changed_subsections[1].children = changed_subsection_1a_items
        changed_subsections[2].children = changed_subsection_3_items

        self.assertEqual([
            'subsec_1',
            'subsec_1__list_1__item_a',
            'subsec_1__list_1__item_aA',
            'subsec_1__list_1__item_aA__list_1__item_i',
            'subsec_1__list_1__item_aA__list_1__item_ii',
            'subsec_1__list_1__item_b',
            'subsec_2',
            'subsec_2__list_1__item_a',
            'subsec_2__list_1__item_b',
            # 1A will be worked out as after 2 if 2 is removed and 1A is inserted
            'subsec_1A',
            'subsec_1A__list_1__item_a',
            'subsec_1A__list_1__item_b',
            'subsec_3',
            'subsec_3__list_1__item_a',
            'subsec_3__list_1__item_b',
            'subsec_3__list_1__item_c',
        ], self.run_test_insert_nested([deepcopy(original_subsections), deepcopy(changed_subsections)]))

        self.assertEqual([
            'subsec_1',
            'subsec_1__list_1__item_a',
            'subsec_1__list_1__item_aA',
            'subsec_1__list_1__item_b',
            'subsec_1A',
            'subsec_1A__list_1__item_a',
            'subsec_1A__list_1__item_a__list_1__item_i',
            'subsec_1A__list_1__item_a__list_1__item_ii',
            'subsec_1A__list_1__item_b',
            'subsec_2',
            'subsec_2__list_1__item_a',
            'subsec_2__list_1__item_b',
            'subsec_2__list_1__item_b__list_1__item_A',
            'subsec_2__list_1__item_b__list_1__item_B',
            'subsec_2__list_1__item_c',
            'subsec_3',
            'subsec_3__list_1__item_a',
            'subsec_3__list_1__item_b',
        ], self.run_test_insert_nested(
            [deepcopy(original_subsections), deepcopy(removed_subsections), deepcopy(inserted_subsections)]
        ))

        self.assertEqual([
            'subsec_1',
            'subsec_1__list_1__item_a',
            'subsec_1__list_1__item_aA',
            'subsec_1__list_1__item_b',
            'subsec_1A',
            'subsec_1A__list_1__item_a',
            'subsec_1A__list_1__item_a__list_1__item_i',
            'subsec_1A__list_1__item_a__list_1__item_ii',
            'subsec_1A__list_1__item_b',
            'subsec_2',
            'subsec_2__list_1__item_a',
            'subsec_2__list_1__item_b',
            'subsec_2__list_1__item_b__list_1__item_A',
            'subsec_2__list_1__item_b__list_1__item_B',
            'subsec_2__list_1__item_c',
            'subsec_3',
            'subsec_3__list_1__item_a',
            'subsec_3__list_1__item_b',
        ], self.run_test_insert_nested(
            [deepcopy(original_subsections), deepcopy(inserted_subsections), deepcopy(removed_subsections)]
        ))

        self.assertEqual([
            'subsec_1',
            'subsec_1__list_1__item_a',
            'subsec_1__list_1__item_aA',
            'subsec_1__list_1__item_aA__list_1__item_i',
            'subsec_1__list_1__item_aA__list_1__item_ii',
            'subsec_1__list_1__item_b',
            'subsec_1A',
            'subsec_1A__list_1__item_a',
            'subsec_1A__list_1__item_a__list_1__item_i',
            'subsec_1A__list_1__item_a__list_1__item_ii',
            'subsec_1A__list_1__item_b',
            'subsec_2',
            'subsec_2__list_1__item_a',
            'subsec_2__list_1__item_b',
            'subsec_2__list_1__item_b__list_1__item_A',
            'subsec_2__list_1__item_b__list_1__item_B',
            'subsec_2__list_1__item_c',
            'subsec_3',
            'subsec_3__list_1__item_a',
            'subsec_3__list_1__item_b',
            'subsec_3__list_1__item_c',
        ], self.run_test_insert_nested(
            [deepcopy(original_subsections), deepcopy(inserted_subsections),
             deepcopy(removed_subsections), deepcopy(changed_subsections)]
        ))

    def test_removed_basic(self):
        pit_1_provisions = ['1', '2', '3', '4', '5', '6']
        pit_2_provisions = ['1', '3', '4']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provision_ids = [p.id for p in provisions]
        self.assertEqual(provision_ids, [
            'section-1',
            'section-2',
            'section-3',
            'section-4',
            'section-5',
            'section-6',
        ])

    def test_removed_inserted(self):
        pit_1_provisions = ['1', '2', '3', '4', '5']
        pit_2_provisions = ['3', '4', '4A', '4B', '4C', '4D', '5', '5A']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provision_ids = [p.id for p in provisions]
        self.assertEqual(provision_ids, [
            'section-1',
            'section-2',
            'section-3',
            'section-4',
            'section-4A',
            'section-4B',
            'section-4C',
            'section-4D',
            'section-5',
            'section-5A',
        ])

        # provisions removed, then others inserted
        pit_1_provisions = ['1', '2', '3', '4', '5']
        pit_2_provisions = ['1', '4', '5']
        pit_3_provisions = ['1', '4', '4A', '4B', '4C', '5']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions, pit_3_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provision_ids = [p.id for p in provisions]
        self.assertEqual(provision_ids, [
            'section-1',
            'section-2',
            'section-3',
            'section-4',
            'section-4A',
            'section-4B',
            'section-4C',
            'section-5',
        ])

        # provisions removed, others inserted at same index
        # unfortunately in this case 2A to 2C will be inserted after 3,
        # because they might as well be 4A to 4C – there's no way to know for sure
        # when a new provision is inserted at the index of a removed one.
        pit_1_provisions = ['1', '2', '3', '4', '5']
        pit_3_provisions = ['1', '2', '2A', '2B', '2C', '5']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions, pit_3_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provision_ids = [p.id for p in provisions]
        self.assertEqual(provision_ids, [
            'section-1',
            'section-2',
            'section-3',
            'section-4',
            'section-2A',
            'section-2B',
            'section-2C',
            'section-5',
        ])

    def test_inserted_removed_edge(self):
        # new provision inserted at same index as a removed provision
        pit_1_provisions = ['1', '2', '3']
        pit_2_provisions = ['1', 'XX', '3']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provision_ids = [p.id for p in provisions]
        self.assertEqual(provision_ids, [
            'section-1',
            'section-2',
            'section-XX',
            'section-3',
        ])

        # provision inserted, removed, another inserted
        pit_1_provisions = ['1', '2', '3']
        pit_2_provisions = ['1', '2', '2A', '2B', '3']
        pit_3_provisions = ['2C', '3']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions, pit_3_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provision_ids = [p.id for p in provisions]
        self.assertEqual(provision_ids, [
            'section-1',
            'section-2',
            'section-2A',
            'section-2B',
            'section-2C',
            'section-3',
        ])

        # absolute garbage
        # pit 2's provisions will be tacked onto the end
        pit_1_provisions = ['1', '2', '3', '4', '5', '6']
        pit_2_provisions = ['3A', '3B', 'X', 'Y', 'Z']
        pit_3_provisions = ['1', '2', '3', '4', '4A', '4B', '5', '6']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions, pit_3_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provision_ids = [p.id for p in provisions]
        self.assertEqual(provision_ids, [
            'section-1',
            'section-2',
            'section-3',
            'section-4',
            'section-4A',
            'section-4B',
            'section-5',
            'section-6',
            'section-3A',
            'section-3B',
            'section-X',
            'section-Y',
            'section-Z',
        ])
