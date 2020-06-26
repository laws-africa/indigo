# -*- coding: utf-8 -*-
from unittest import TestCase

import lxml.html

from indigo.analysis.differ import AttributeDiffer


def as_tree(html):
    return lxml.html.fromstring(html)


def as_html(tree):
    return lxml.html.tostring(tree, encoding='utf-8').decode('utf-8')


class AttributeDifferTestCase(TestCase):
    def setUp(self):
        self.differ = AttributeDiffer()

    def test_text_changed(self):
        old = as_tree('<p>abc 123</p>')
        new = as_tree('<p>def 456</p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            as_html(diff),
            '<p><span class="diff-pair"><del>abc 123</del><ins>def 456</ins></span></p>',
        )

    def test_text_partially_changed(self):
        old = as_tree('<p>some old text</p>')
        new = as_tree('<p>some new text</p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            as_html(diff),
            '<p>some <span class="diff-pair"><del>old</del><ins>new</ins></span> text</p>',
        )

    def test_text_partially_changed_with_elements(self):
        old = as_tree('<p>some old text <b>no change</b> text <i>no change</i></p>')
        new = as_tree('<p>some new text <b>no change</b> text <i>no change</i></p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            as_html(diff),
            '<p>some <span class="diff-pair"><del>old</del><ins>new</ins></span> text <b>no change</b> text <i>no change</i></p>',
        )

    def test_tail_changed(self):
        old = as_tree('<p>something <b>bold</b> 123 xx <i>and</i> same </p>')
        new = as_tree('<p>something <b>bold</b> 456 xx <i>and</i> same </p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            as_html(diff),
            '<p>something <b>bold</b> <span class="diff-pair"><del>123</del><ins>456</ins></span> xx <i>and</i> same </p>',
        )

    def test_inline_tag_removed(self):
        old = as_tree('<p>Some text <b>bold text</b> and a tail.</p>')
        new = as_tree('<p>Some text bold text and a tail.</p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            as_html(diff),
            '<p>Some text <ins>bold text and a tail.</ins><b class="del ">bold text</b> and a tail.</p>',
        )

    def test_inline_tag_added(self):
        old = as_tree('<p>Some text bold text and a tail.</p>')
        new = as_tree('<p>Some text <b>bold text</b> and a tail.</p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            as_html(diff),
            '<p>Some text <span class="diff-pair"><del>bold text and a tail.</del><ins>&#xA0;</ins></span><b class="ins ">bold text</b><ins> and a tail.</ins></p>',
        )

    def test_diff_lists_deleted(self):
        diffs = self.differ.diff_lists('test', 'Test', ['1', '2', '3'], ['1', '3'])
        self.assertEqual({
            'attr': 'test',
            'title': 'Test',
            'type': 'list',
            'changes': [{
                'html_new': '1',
                'html_old': '1'
            }, {
                'html_new': '',
                'html_old': '<del>2</del>',
                'new': None,
                'old': '2'
            }, {
                'html_new': '3',
                'html_old': '3'
            }]},
            diffs)

    def test_diff_lists_empty(self):
        diffs = self.differ.diff_lists('test', 'Test', ['1', '2', '3'], [])
        self.assertEqual({
            'attr': 'test',
            'title': 'Test',
            'type': 'list',
            'changes': [{
                'html_new': '',
                'html_old': '<del>1</del>',
                'new': None,
                'old': '1'
            }, {
                'html_new': '',
                'html_old': '<del>2</del>',
                'new': None,
                'old': '2'
            }, {
                'html_new': '',
                'html_old': '<del>3</del>',
                'new': None,
                'old': '3'
            }]},
            diffs)

    def test_diff_lists_added(self):
        diffs = self.differ.diff_lists('test', 'Test', ['1', '3'], ['1', '2', '3'])
        self.assertEqual({
            'attr': 'test',
            'title': 'Test',
            'type': 'list',
            'changes': [{
                'html_new': '1',
                'html_old': '1'
            }, {
                'html_new': '<ins>2</ins>',
                'html_old': '',
                'new': '2',
                'old': None
            }, {
                'html_new': '3',
                'html_old': '3'
            }]},
            diffs)
