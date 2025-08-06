from unittest import TestCase

from xmldiff.formatting import XMLFormatter

from indigo_lib.differ import AKNHTMLDiffer


class AKNHTMLDifferTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.differ = AKNHTMLDiffer()

    def test_text_changed(self):
        diff = self.differ.diff_html_str(
            '<p>abc 123</p>',
            '<p>def 456</p>'
        )

        self.assertEqual(
            '<p><span class="diff-pair"><del>abc 123</del><ins>def 456</ins></span></p>',
            diff,
        )

    def test_text_partially_changed(self):
        diff = self.differ.diff_html_str(
            '<p>some old text</p>',
            '<p>some new text</p>'
        )

        self.assertEqual(
            '<p>some <span class="diff-pair"><del>old</del><ins>new</ins></span> text</p>',
            diff,
        )

    def test_text_partially_changed_with_elements(self):
        diff = self.differ.diff_html_str(
            '<p>some old text <b>no change</b> text <i>no change</i></p>',
            '<p>some new text <b>no change</b> text <i>no change</i></p>'
        )

        self.assertEqual(
            '<p>some <span class="diff-pair"><del>old</del><ins>new</ins></span> text <b>no change</b> text <i>no change</i></p>',
            diff,
        )

    def test_tail_changed(self):
        diff = self.differ.diff_html_str(
            '<p>something <b>bold</b> 123 xx <i>and</i> same </p>',
            '<p>something <b>bold</b> 456 xx <i>and</i> same </p>'
        )

        self.assertEqual(
            '<p>something <b>bold</b> <span class="diff-pair"><del>123</del><ins>456</ins></span> xx <i>and</i> same </p>',
            diff,
        )

    def test_inline_tag_removed(self):
        diff = self.differ.diff_html_str(
            '<p>Some text <b>bold text</b> and a tail.</p>',
            '<p>Some text bold text and a tail.</p>'
        )

        self.assertEqual(
            '<p>Some text <ins>bold text and a tail.</ins><b class="del ">bold text</b> and a tail.</p>',
            diff,
        )

    def test_inline_tag_added(self):
        diff = self.differ.diff_html_str(
            '<p>Some text bold text and a tail.</p>',
            '<p>Some text <b>bold text</b> and a tail.</p>'
        )

        self.assertEqual(
            '<p>Some text <span class="diff-pair"><del>bold text and a tail.</del><b class="ins ">bold text</b></span><ins> and a tail.</ins></p>',
            diff,
        )

    def test_more_refs_added(self):
        """ When adding a new ref to a p tag, the other refs should not be considered different.
        """
        diff = self.differ.diff_html_str(
            '<p class="akn-p">Some text <a class="akn-ref" href="https://example.com" data-href="https://example.com" id="ref_1" data-eid="ref_1">link</a>.</p>',
            '<p class="akn-p">Some text <a class="akn-ref" href="https://example.com" data-href="https://example.com" id="ref_1" data-eid="ref_1">new</a> and'
            ' <a class="akn-ref" href="https://example.com" data-href="https://example.com" id="ref_2" data-eid="ref_2">link</a>.</p>'
        )

        self.assertEqual(
            '<p class="akn-p">Some text <a class="ins akn-ref" href="https://example.com">new</a><ins> and </ins><a class="akn-ref" href="https://example.com">link</a>.</p>',
            diff,
        )

    def test_p_inserted(self):
        diff = self.differ.diff_html_str(
            '<p>First p.</p><p>Second p.</p>',
            '<p>First p.</p><p>Inserted text.</p><p>Second p.</p>',
        )
        self.assertEqual(
            '<div><p>First p.</p><p><span class="diff-pair"><del>Second p</del><ins>Inserted text</ins></span>.</p><p class="ins ">Second p.</p></div>',
            diff,
        )

    def test_p_inserted_with_ids(self):
        diff = self.differ.diff_html_str(
            '<p id="p_1">First p.</p><p id="p_2">Second p.</p>',
            '<p id="p_1">First p.</p><p id="p_2">Inserted text.</p><p id="p_3">Second p.</p>',
        )
        self.assertEqual(
            '<div><p id="p_1">First p.</p><p id="p_2"><span class="diff-pair"><del>Second p</del><ins>Inserted text</ins></span>.</p><p class="ins " id="p_3">Second p.</p></div>',
            diff,
        )

    def test_inline_tag_with_id(self):
        diff = self.differ.diff_html_str("""
<span class="akn-content"
  ><span class="akn-p" id="p_1">Some text at the start.</span
  ><span class="akn-p" id="p_2"
      >Prefix <span class="akn-remark">A remark <a href="#foo" id="p_2__ref_1">a link</a></span>.</span
  ></span
>
""", """
<span class="akn-content"
  ><span class="akn-p" id="p_1">Some text at the start.</span
  ><span class="akn-p" id="p_2">New text that was added.</span
  ><span class="akn-p" id="p_3"
      >Prefix <span class="akn-remark">A remark <a href="#foo" id="p_3__ref_1">a link</a></span>.</span
  ></span
>
"""
        )

        self.assertMultiLineEqual(
            """
<span class="akn-content"><span class="akn-p" id="p_1">Some text at the start.</span><span class="akn-p" id="p_2"><span class="diff-pair"><del>Prefix&#xA0;</del><ins>&#xA0;</ins></span><span class="del akn-remark">A remark <a href="#foo" id="p_2__ref_1">a link</a></span><ins>New text that was added</ins>.</span><span class="ins akn-p" id="p_3">Prefix <span class="akn-remark">A remark <a href="#foo" id="p_3__ref_1">a link</a></span>.</span></span>
""".strip(),
            diff.strip()
        )

    def test_inline_a_with_id_should_be_ignored(self):
        diff = self.differ.diff_html_str("""
    <span class="akn-content"
      ><span class="akn-p" id="p_1">Some text at the start.</span
      ><span class="akn-p" id="p_2"
          >Prefix <span class="akn-remark">A remark <a href="#foo" id="ref_OLD">a link</a></span>.</span
      ></span
    >
    """, """
    <span class="akn-content"
      ><span class="akn-p" id="p_1">Some text at the start.</span
      ><span class="akn-p" id="p_2"
          >Prefix <span class="akn-remark">A remark <a href="#foo" id="ref_NEW">a link</a></span>.</span
      ></span
    >
    """)

        self.assertMultiLineEqual("""
<span class="akn-content"><span class="akn-p" id="p_1">Some text at the start.</span><span class="akn-p" id="p_3">Prefix <span class="del akn-remark">A remark <a href="#foo" id="ref_OLD">a link</a></span><span class="ins akn-remark">A remark <a href="#foo" id="ref_NEW">a link</a></span>.</span></span>
""".strip(),
            diff.strip()
        )

    def test_remarks(self):
        diff = self.differ.diff_html_str(
            """
<span class="akn-content"
  ><span class="akn-p" id="chp_3__sec_4__p_1" data-eId="chp_3__sec_4__p_1"
    >In this Act, unless the context otherwise indicates—</span
  ><span
    class="akn-p"
    data-refersTo="#term-Court"
    id="chp_3__sec_4__p_2"
    data-eId="chp_3__sec_4__p_2"
    >"<span
      class="akn-def"
      data-refersTo="#term-Court"
      id="chp_3__sec_4__p_2__def_1"
      data-eId="chp_3__sec_4__p_2__def_1"
      >Court</span
    >" means a provincial or local division of the Supreme Court of South Africa or any judge thereof;</span
  ><span
    class="akn-p"
    data-refersTo="#term-deletion"
    id="chp_3__sec_4__p_3"
    data-eId="chp_3__sec_4__p_3"
    >"<span
      class="akn-def"
      data-refersTo="#term-deletion"
      id="chp_3__sec_4__p_3__def_1"
      data-eId="chp_3__sec_4__p_3__def_1"
      >deletion</span
    >" means a deletion, cancellation or obliteration in whatever manner effected, excluding a deletion, cancellation or obliteration that contemplates the revocation of the entire will;</span
  ><span class="akn-p" id="chp_3__sec_4__p_4" data-eId="chp_3__sec_4__p_4"
    ><span class="akn-remark" data-status="editorial"
      >[definition of "deletion" inserted by section 2(b) of <a
        data-href="/akn/za/act/1992/43"
        class="akn-ref"
        href="http://localhost:8000/resolver/resolve/akn/za/act/1992/43"
        id="chp_3__sec_4__p_4__ref_1"
        >Act 43 of 1992</a
      >]</span
    ></span
  ></span
>
            """,
            """
<span class="akn-content"
  ><span class="akn-p" id="chp_3__sec_4__p_1" data-eId="chp_3__sec_4__p_1"
    >In this Act, unless the context otherwise indicates—</span
  ><span
    class="akn-p"
    data-refersTo="#term-Court"
    id="chp_3__sec_4__p_2"
    data-eId="chp_3__sec_4__p_2"
    >"<span
      class="akn-def"
      data-refersTo="#term-Court"
      id="chp_3__sec_4__p_2__def_1"
      data-eId="chp_3__sec_4__p_2__def_1"
      >Court</span
    >" means a provincial or local division of the Supreme Court of South Africa or any judge thereof;</span
  ><span class="akn-p" id="chp_3__sec_4__p_3" data-eId="chp_3__sec_4__p_3"
    ><span class="akn-remark" data-status="editorial"
      >[definition of "court" amended by <a
        data-href="/akn/za/act/1996/49"
        class="akn-ref"
        href="http://localhost:8000/resolver/resolve/akn/za/act/1996/49"
        id="chp_3__sec_4__p_3__ref_1"
        data-eId="chp_3__sec_4__p_3__ref_1"
        >Act 49 of 1996</a
      >]</span
    ></span
  ><span
    class="akn-p"
    data-refersTo="#term-deletion"
    id="chp_3__sec_4__p_4"
    data-eId="chp_3__sec_4__p_4"
    >"<span
      class="akn-def"
      data-refersTo="#term-deletion"
      id="chp_3__sec_4__p_4__def_1"
      data-eId="chp_3__sec_4__p_4__def_1"
      >deletion</span
    >" means a deletion, cancellation or obliteration in whatever manner effected, excluding a deletion, cancellation or obliteration that contemplates the revocation of the entire will;</span
  ><span class="akn-p" id="chp_3__sec_4__p_5" data-eId="chp_3__sec_4__p_5"
    ><span class="akn-remark" data-status="editorial"
      >[definition of "deletion" inserted by section 2(b) of <a
        data-href="/akn/za/act/1992/43"
        class="akn-ref"
        href="http://localhost:8000/resolver/resolve/akn/za/act/1992/43"
        id="chp_3__sec_4__p_5__ref_1"
        >Act 43 of 1992</a
      >]</span
    ></span
  ></span
>
            """
        )

        # TODO: this diff is bad, it shouldn't have the <ins> and <del> tags in the remarks.
        self.assertMultiLineEqual(
            """
<span class="akn-content"><span class="akn-p" data-eid="chp_3__sec_4__p_1" id="chp_3__sec_4__p_1">In this Act, unless the context otherwise indicates&#x2014;</span><span class="akn-p" data-refersto="#term-Court" data-eid="chp_3__sec_4__p_2" id="chp_3__sec_4__p_2">"<span class="akn-def" data-refersto="#term-Court">Court</span>" means a provincial or local division of the Supreme Court of South Africa or any judge thereof;</span><span class="ins akn-p" data-eid="chp_3__sec_4__p_3" id="chp_3__sec_4__p_3"><span class="akn-remark">[definition of "court" amended by <a data-href="/akn/za/act/1996/49" class="akn-ref" href="http://localhost:8000/resolver/resolve/akn/za/act/1996/49" data-eid="chp_3__sec_4__p_3__ref_1" id="chp_3__sec_4__p_3__ref_1">Act 49 of 1996</a>]</span></span><span class="akn-p" data-refersto="#term-deletion" data-eid="chp_3__sec_4__p_4" id="chp_3__sec_4__p_4">"<span class="akn-def" data-refersto="#term-deletion">deletion</span>" means a deletion, cancellation or obliteration in whatever manner effected, excluding a deletion, cancellation or obliteration that contemplates the revocation of the entire will;</span><span class="akn-p" data-eid="chp_3__sec_4__p_5" id="chp_3__sec_4__p_5"><span class="del akn-remark">[definition of "deletion" inserted by section 2(b) of <a data-href="/akn/za/act/1992/43" class="akn-ref" href="http://localhost:8000/resolver/resolve/akn/za/act/1992/43" data-eid="chp_3__sec_4__p_4__ref_1" id="chp_3__sec_4__p_4__ref_1">Act 43 of 1992</a>]</span><span class="ins akn-remark">[definition of "deletion" inserted by section 2(b) of <a data-href="/akn/za/act/1992/43" class="akn-ref" href="http://localhost:8000/resolver/resolve/akn/za/act/1992/43" data-eid="chp_3__sec_4__p_5__ref_1" id="chp_3__sec_4__p_5__ref_1">Act 43 of 1992</a>]</span></span></span>
""".strip(),
            diff.strip()
        )
