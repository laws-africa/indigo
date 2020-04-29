# -*- coding: utf-8 -*-
from dotmap import DotMap
from django.test import TestCase

from indigo.analysis.toc.base import TOCElement, TOCBuilderBase
from indigo_api.templatetags.indigo import make_beautiful


class BeautifulProvisionsTestCase(TestCase):
    def setUp(self):
        self.commenceable_provisions = [TOCElement(
            element=None, component=None, type_='section', id_=f'section-{number}', num=f'{number}.'
        ) for number in range(1, 31)]
        self.toc_plugin = TOCBuilderBase()

    def test_beautiful_provisions_basic(self):
        provisions = ['section-1', 'section-2', 'section-3', 'section-4']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 1–4')

        provisions = ['section-2', 'section-3', 'section-4', 'section-5']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 2–5')

        provisions = ['section-1', 'section-2', 'section-3']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 1–3')

        provisions = ['section-1', 'section-3', 'section-4', 'section-5', 'section-6']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 1, section 3–6')

        provisions = ['section-1', 'section-2', 'section-3', 'section-4', 'section-5', 'section-7']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 1–5, section 7')

        provisions = ['section-1', 'section-3', 'section-4', 'section-5', 'section-6', 'section-8']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 1, section 3–6, section 8')

        provisions = ['section-1', 'section-4', 'section-5', 'section-6', 'section-7', 'section-8', 'section-9', 'section-10', 'section-11', 'section-12', 'section-14', 'section-16', 'section-20', 'section-21']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 1, section 4–12, section 14, section 16, section 20, section 21')

    def test_one_item(self):
        provisions = ['section-23']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 23')

    def test_two_items(self):
        provisions = ['section-23', 'section-25']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 23, section 25')

    def test_three_items(self):
        provisions = ['section-23', 'section-24', 'section-25']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 23–25')

    def test_one_excluded(self):
        commenceable_provisions = [
            TOCElement(element=None, component=None, type_='section', id_=f'section-{number}', num=f'{number}.') for
            number in range(1, 4)]

        provisions = ['section-1', 'section-2']
        description = make_beautiful(provisions, commenceable_provisions)
        self.assertEqual(description, 'section 1, section 2')

        provisions = ['section-2', 'section-3']
        description = make_beautiful(provisions, commenceable_provisions)
        self.assertEqual(description, 'section 2, section 3')

    def test_chapter(self):
        provisions = ['section-2', 'section-3', 'chapter-2', 'section-4', 'section-5']
        commenceable_provisions = [
            TOCElement(element=None, component=None, type_='section', id_=f'section-{number}', num=f'{number}.') for
            number in range(1, 4)]
        commenceable_provisions.append(TOCElement(element=None, component=None, type_='chapter', id_='chapter-2', num='2'))
        commenceable_provisions = commenceable_provisions + [
            TOCElement(element=None, component=None, type_='section', id_=f'section-{number}', num=f'{number}.') for
            number in range(4, 21)]
        description = make_beautiful(provisions, commenceable_provisions)
        self.assertEqual(description, 'section 2, section 3, chapter 2, section 4, section 5')

    def test_provisions_out_of_sync(self):
        provisions = ['section-29', 'section-30', 'section-31', 'section-32']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 29, section 30')

        provisions = ['section-31', 'section-32', 'section-33', 'section-34']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, '')

    def test_inserted(self):
        pit_1_provisions = ['1', '2', '3']
        pit_2_provisions = ['1', '1A', '2', '2A', '3', '3A']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provisions = [p.id for p in provisions]
        self.assertEqual(provisions, [
            'section-1',
            'section-1A',
            'section-2',
            'section-2A',
            'section-3',
            'section-3A',
        ])

    def test_removed_basic(self):
        pit_1_provisions = ['1', '2', '3', '4', '5', '6']
        pit_2_provisions = ['1', '3', '4']
        provisions = []
        id_set = set()
        for pit in [pit_1_provisions, pit_2_provisions]:
            items = [DotMap(id=f'section-{p}') for p in pit]
            self.toc_plugin.insert_provisions(provisions, id_set, items)
        provisions = [p.id for p in provisions]
        self.assertEqual(provisions, [
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
        provisions = [p.id for p in provisions]
        self.assertEqual(provisions, [
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
        provisions = [p.id for p in provisions]
        self.assertEqual(provisions, [
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
        provisions = [p.id for p in provisions]
        self.assertEqual(provisions, [
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
        provisions = [p.id for p in provisions]
        self.assertEqual(provisions, [
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
        provisions = [p.id for p in provisions]
        self.assertEqual(provisions, [
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
        provisions = [p.id for p in provisions]
        self.assertEqual(provisions, [
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
