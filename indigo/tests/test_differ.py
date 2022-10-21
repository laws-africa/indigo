from django.test import TestCase

import lxml.html

from indigo.analysis.differ import AttributeDiffer


def as_tree(html):
    return lxml.html.fromstring(html)


def as_html(tree):
    return lxml.html.tostring(tree, encoding='utf-8').decode('utf-8')


class AttributeDifferTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.differ = AttributeDiffer()

    def test_text_changed(self):
        old = as_tree('<p>abc 123</p>')
        new = as_tree('<p>def 456</p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            '<p><span class="diff-pair"><del>abc 123</del><ins>def 456</ins></span></p>',
            as_html(diff),
        )

    def test_text_partially_changed(self):
        old = as_tree('<p>some old text</p>')
        new = as_tree('<p>some new text</p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            '<p>some <span class="diff-pair"><del>old</del><ins>new</ins></span> text</p>',
            as_html(diff),
        )

    def test_text_partially_changed_with_elements(self):
        old = as_tree('<p>some old text <b>no change</b> text <i>no change</i></p>')
        new = as_tree('<p>some new text <b>no change</b> text <i>no change</i></p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            '<p>some <span class="diff-pair"><del>old</del><ins>new</ins></span> text <b>no change</b> text <i>no change</i></p>',
            as_html(diff),
        )

    def test_tail_changed(self):
        old = as_tree('<p>something <b>bold</b> 123 xx <i>and</i> same </p>')
        new = as_tree('<p>something <b>bold</b> 456 xx <i>and</i> same </p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            '<p>something <b>bold</b> <span class="diff-pair"><del>123</del><ins>456</ins></span> xx <i>and</i> same </p>',
            as_html(diff),
        )

    def test_inline_tag_removed(self):
        old = as_tree('<p>Some text <b>bold text</b> and a tail.</p>')
        new = as_tree('<p>Some text bold text and a tail.</p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            '<p>Some text <ins>bold text and a tail.</ins><b class="del ">bold text</b> and a tail.</p>',
            as_html(diff),
        )

    def test_inline_tag_added(self):
        old = as_tree('<p>Some text bold text and a tail.</p>')
        new = as_tree('<p>Some text <b>bold text</b> and a tail.</p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            as_html(diff),
            '<p>Some text <span class="diff-pair"><del>bold text and a tail.</del><ins>&#xA0;</ins></span><b class="ins ">bold text</b><ins> and a tail.</ins></p>',
        )

    def test_more_refs_added(self):
        """ When adding a new ref to a p tag, the other refs should not be considered different.
        """
        old = as_tree('<p class="akn-p">Some text <a class="akn-ref" href="https://example.com" data-href="https://example.com" id="ref_1" data-eid="ref_1">link</a>.</p>')
        new = as_tree('<p class="akn-p">Some text <a class="akn-ref" href="https://example.com" data-href="https://example.com" id="ref_1" data-eid="ref_1">new</a> and'
                      ' <a class="akn-ref" href="https://example.com" data-href="https://example.com" id="ref_2" data-eid="ref_2">link</a>.</p>')
        n_changes, diff = self.differ.diff_document_html(old, new)

        self.assertEqual(
            '<p class="akn-p">Some text <a class="ins akn-ref" href="https://example.com">new</a><ins> and </ins><a class="akn-ref" href="https://example.com">link</a>.</p>',
            as_html(diff),
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

    def test_diff_list_item_inserted(self):
        diffs = self.differ.diff_lists(
            'test', 'Test',
            ['2020-03-18: No commencing work: section 1, section 2, section 3, section 4, section 5, section 6, section 7, section 8, section 9, section 10, section 11, section 12, Chapter 1, section 1, section ...',
             '2020-03-26: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 1, section 1A; Chapter 2, section 11A, section 11B, section 11C, section 11D, section 11E, section 11F, sec...',
             '2020-04-02: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 3, section 11H, section 11I',
             '2020-04-16: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 2, section 11CA; Chapter 4, section 11J, section 11K'],
            ['2020-03-18: No commencing work: section 1–12, Chapter 1, section 1(a), 1(b), section 2, section 3–7, section 8(1), 8(2), 8(3), 8(4), 8(5), section 9, section 10(1), 10(2), 10(3), 10(4), 10(5), 10(6...',
             '2020-03-25: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 1, section 1(a), 1(b), 1(c), section 1A; Chapter 2, section 11A, section 11B(1)(a)(i), 11B(1)(a)(ii), 11B(1...',
             '2020-03-26: Disaster Management Act: Regulations relating to COVID-19: Amendment: no provisions',
             '2020-04-02: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 3, section 11H, section 11I',
             '2020-04-16: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 2, section 11CA; Chapter 4, section 11J–11K']
        )

        self.assertEqual({
            'attr': 'test',
            'title': 'Test',
            'changes': [{
                'old': '2020-03-18: No commencing work: section 1, section 2, section 3, section 4, section 5, section 6, section 7, section 8, section 9, section 10, section 11, section 12, Chapter 1, section 1, section ...',
                'new': '2020-03-18: No commencing work: section 1–12, Chapter 1, section 1(a), 1(b), section 2, section 3–7, section 8(1), 8(2), 8(3), 8(4), 8(5), section 9, section 10(1), 10(2), 10(3), 10(4), 10(5), 10(6...',
                'html_old': '2020-03-18: No commencing work: section 1<del>, section 2, section 3, section 4, section 5, section 6, section 7, section 8, section 9, section 10, section 11, section </del>12, Chapter 1, section 1<del>, section </del>...',
                'html_new': '2020-03-18: No commencing work: section 1<ins>–</ins>12, Chapter 1, section 1<ins>(a), 1(b), section 2, section 3–7, section 8(1), 8(2), 8(3), 8(4), 8(5), section 9, section 10(1), 10(2), 10(3), 10(4), 10(5), 10(6</ins>...'
            }, {
                'old': '2020-03-26: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 1, section 1A; Chapter 2, section 11A, section 11B, section 11C, section 11D, section 11E, section 11F, sec...',
                'new': '2020-03-25: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 1, section 1(a), 1(b), 1(c), section 1A; Chapter 2, section 11A, section 11B(1)(a)(i), 11B(1)(a)(ii), 11B(1...',
                'html_old': '2020-03-2<del>6</del>: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 1, section 1A; Chapter 2, section 11A, section 11B<del>, section 11C, section 11D, section 11E, section 11F, sec</del>...',
                'html_new': '2020-03-2<ins>5</ins>: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 1, section 1<ins>(a), 1(b), 1(c), section 1</ins>A; Chapter 2, section 11A, section 11B<ins>(1)(a)(i), 11B(1)(a)(ii), 11B(1</ins>...'
            }, {
                'old': None,
                'new': '2020-03-26: Disaster Management Act: Regulations relating to COVID-19: Amendment: no provisions',
                'html_old': '',
                'html_new': '<ins>2020-03-26: Disaster Management Act: Regulations relating to COVID-19: Amendment: no provisions</ins>'
            }, {
                'html_old': '2020-04-02: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 3, section 11H, section 11I',
                'html_new': '2020-04-02: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 3, section 11H, section 11I'
            }, {
                'old': '2020-04-16: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 2, section 11CA; Chapter 4, section 11J, section 11K',
                'new': '2020-04-16: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 2, section 11CA; Chapter 4, section 11J–11K',
                'html_old': '2020-04-16: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 2, section 11CA; Chapter 4, section 11J<del>, section </del>11K',
                'html_new': '2020-04-16: Disaster Management Act: Regulations relating to COVID-19: Amendment: Chapter 2, section 11CA; Chapter 4, section 11J<ins>–</ins>11K'
            }],
            'type': 'list'
        }, diffs)
