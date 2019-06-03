# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unittest import TestCase

from lxml import etree

from indigo.analysis.differ import unwrap_element


class XMLUtilsTestCase(TestCase):
    def test_unwrap_elem_first_child_complex(self):
        root = etree.fromstring('<p>text <term>content <b>child1</b> <i>child2</i> endterm</term> tail</p>')
        term = root.find('term')
        unwrap_element(term)

        actual = etree.tostring(root)
        self.assertMultiLineEqual(
            '<p>text content <b>child1</b> <i>child2</i> endterm tail</p>',
            actual,
        )

    def test_unwrap_elem_first_child_simple(self):
        root = etree.fromstring('<p>text <term>content</term> tail</p>')
        term = root.find('term')
        unwrap_element(term)

        actual = etree.tostring(root)
        self.assertMultiLineEqual(
            '<p>text content tail</p>',
            actual,
        )

    def test_unwrap_elem_second_child_complex(self):
        root = etree.fromstring('<p>text <term>first</term> and <term>content <b>child1</b> <i>child2</i> endterm</term> tail</p>')
        term = root.getchildren()[1]
        unwrap_element(term)

        actual = etree.tostring(root)
        self.assertMultiLineEqual(
            '<p>text <term>first</term> and content <b>child1</b> <i>child2</i> endterm tail</p>',
            actual,
        )

