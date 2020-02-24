# -*- coding: utf-8 -*-
from django.test import TestCase

from indigo.analysis.toc.base import TOCElement
from indigo_api.templatetags.indigo import make_beautiful


class BeautifulProvisionsTestCase(TestCase):
    def setUp(self):
        self.commenceable_provisions = [TOCElement(element=None, component=None, type_='section', id_=f'section-{number}', num=f'{number}.') for number in range(1, 31)]

    def test_beautiful_provisions_basic(self):
        provisions = ['section-1', 'section-2', 'section-3', 'section-4']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 1–4')

        provisions = ['section-2', 'section-3', 'section-4', 'section-5']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 2–5')

        provisions = ['section-1', 'section-2', 'section-3']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 1, section 2, section 3')

        provisions = ['section-1', 'section-4', 'section-5', 'section-6', 'section-7', 'section-8', 'section-9', 'section-10', 'section-11', 'section-12', 'section-14', 'section-16', 'section-20', 'section-21']
        description = make_beautiful(provisions, self.commenceable_provisions)
        self.assertEqual(description, 'section 1, section 4–12, section 14, section 16, section 20, section 21')

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
