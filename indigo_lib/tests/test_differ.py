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

    def test_formatting_add_remove(self):
        diff = self.differ.diff_html_str(
            '<p>some text <b>with bold</b> text and a tail.</p>',
            '<p>some text with bold text <i>and a tail.</i></p>'
        )

        self.assertEqual(
            '<p>some text <span class="diff-pair"><del><b>with bold</b></del><ins>with bold</ins></span> text <span class="diff-pair"><del>and a tail.</del><ins><i>and a tail.</i></ins></span></p>',
            diff,
        )

    def test_formatting_changes(self):
        diff = self.differ.diff_html_str(
            '<p>some text <b>with bold</b> text and a tail.</p>',
            '<p>some text <i>with bold</i> text and a tail.</p>'
        )

        self.assertEqual(
            '<p>some text <span class="diff-pair"><del><b>with bold</b></del><ins><i>with bold</i></ins></span> text and a tail.</p>',
            diff,
        )

    def test_formatting_added(self):
        diff = self.differ.diff_html_str(
            '<p>Some text bold text and a tail.</p>',
            '<p>Some text <b>bold text</b> and a tail.</p>'
        )

        self.assertEqual(
            '<p>Some text <span class="diff-pair"><del>bold text</del><ins><b>bold text</b></ins></span> and a tail.</p>',
            diff,
        )

    def test_formatting_and_text_changes(self):
        diff = self.differ.diff_html_str(
            '<p>some text <b>with bold</b> text and a tail.</p>',
            '<p>some text <i>with x bold</i> text and a tail.</p>'
        )

        self.assertEqual(
            '<p>some text <span class="diff-pair"><del><b>with bold</b></del><ins><i>with x bold</i></ins></span> text and a tail.</p>',
            diff,
        )

    def test_formatting_removed(self):
        diff = self.differ.diff_html_str(
            '<p>Some text <b>bold text</b> and a tail.</p>',
            '<p>Some text bold text and a tail.</p>'
        )

        self.assertEqual(
            '<p>Some text <span class="diff-pair"><del><b>bold text</b></del><ins>bold text</ins></span> and a tail.</p>',
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

    def test_inline_tag_and_text_removed(self):
        diff = self.differ.diff_html_str(
            '<p>Some text <b>bold text</b> and a tail.</p>',
            '<p>Some text and a tail.</p>'
        )

        self.assertEqual(
            '<p>Some text <span class="diff-pair"><del><b>bold text</b><ins>bold text</ins></span> and a tail.',
            diff,
        )

    def test_more_refs_added(self):
        """ When adding a new ref to a p tag, the other refs should not be considered different.
        """
        diff = self.differ.diff_html_str(
            '<p class="akn-p">Some text <a class="akn-ref" href="https://example.com" data-href="https://example.com">link</a>.</p>',
            '<p class="akn-p">Some text <a class="akn-ref" href="https://example.com" data-href="https://example.com">new</a> and'
            ' <a class="akn-ref" href="https://example.com" data-href="https://example.com">link</a>.</p>'
        )

        self.assertEqual(
            """
            <p class="akn-p">Some text <a class="ins akn-ref" href="https://example.com" data-href="https://example.com">new</a><ins> and </ins><a class="akn-ref" href="https://example.com" data-href="https://example.com">link</a>.</p>
            """.strip(),
            diff.strip()
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

    def test_preprocess_xml(self):
        xml = self.differ.preprocess_xml_str("""
<section xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" eId="chp_3__sec_4">
  <num>4</num>
  <heading>Heading</heading>
  <content>
    <p eId="chp_3__sec_4__p_1">The word <term>special</term> is a special term.</p>
    <p refersTo="#term-Court" eId="chp_3__sec_4__p_2">"<def refersTo="#term-Court" eId="chp_3__sec_4__p_2__def_1">Court</def>" means a provincial or local division of the Supreme Court of South Africa or any judge thereof;</p>
    <p eId="chp_3__sec_4__p_3"><remark status="editorial">[definition of "court" amended by <ref href="/akn/za/act/1996/49" eId="chp_3__sec_4__p_3__ref_1">Act 49 of 1996</ref>]</remark></p>
  </content>
</section>""")

        self.assertEqual("""
<section xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" eId="chp_3__sec_4">
  <num>4</num>
  <heading>Heading</heading>
  <content>
    <p eId="chp_3__sec_4__p_1">The word special is a special term.</p>
    <p refersTo="#term-Court" eId="chp_3__sec_4__p_2">"<def refersTo="#term-Court">Court</def>" means a provincial or local division of the Supreme Court of South Africa or any judge thereof;</p>
    <p eId="chp_3__sec_4__p_3"><remark status="editorial">[definition of "court" amended by <ref href="/akn/za/act/1996/49">Act 49 of 1996</ref>]</remark></p>
  </content>
</section>""".strip(),
            xml.decode('utf-8').strip()
        )

    def test_inline_text_changed(self):
        diff = self.differ.diff_html_str("""
            <span class="akn-content"
              ><span class="akn-p" id="p_1"
                >Prefix <span class="akn-remark">A remark</span>.</span
              ></span
            >
        """, """
            <span class="akn-content"
              ><span class="akn-p" id="p_1"
                >Prefix <span class="akn-remark">A changed remark</span>.</span
              ></span
            >
        """)

        self.assertMultiLineEqual("""
            <span class="akn-content"><span class="akn-p" id="p_1">Prefix <span class="akn-remark">A <ins>changed </ins>remark</span>.</span></span>
        """.strip(), diff.strip())

    def test_inline_text_changed_nested(self):
        diff = self.differ.diff_html_str("""
            <span class="akn-content"
              ><span class="akn-p" id="p_1"
                >Prefix <span class="akn-remark">A remark <a href="#foo">a link</a></span>.</span
              ></span
            >
        """, """
            <span class="akn-content"
              ><span class="akn-p" id="p_1"
                >Prefix <span class="akn-remark">A remark <a href="#foo">text changed</a></span>.</span
              ></span
            >
        """)

        self.assertMultiLineEqual("""
            <span class="akn-content"><span class="akn-p" id="p_1">Prefix <span class="akn-remark">A remark <a href="#foo" class="del ">a link</a></span><a href="#foo" class="ins ">text changed</a>.</span></span>
        """.strip(), diff.strip())

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
      >deletion</span
    >" means a deletion, cancellation or obliteration in whatever manner effected, excluding a deletion, cancellation or obliteration that contemplates the revocation of the entire will;</span
  ><span class="akn-p" id="chp_3__sec_4__p_4" data-eId="chp_3__sec_4__p_4"
    ><span class="akn-remark" data-status="editorial"
      >[definition of "deletion" inserted by section 2(b) of <a
        data-href="/akn/za/act/1992/43"
        class="akn-ref"
        href="http://localhost:8000/resolver/resolve/akn/za/act/1992/43"
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
      >Court</span
    >" means a provincial or local division of the Supreme Court of South Africa or any judge thereof;</span
  ><span class="akn-p" id="chp_3__sec_4__p_3" data-eId="chp_3__sec_4__p_3"
    ><span class="akn-remark" data-status="editorial"
      >[definition of "court" amended by <a
        data-href="/akn/za/act/1996/49"
        class="akn-ref"
        href="http://localhost:8000/resolver/resolve/akn/za/act/1996/49"
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
      >deletion</span
    >" means a deletion, cancellation or obliteration in whatever manner effected, excluding a deletion, cancellation or obliteration that contemplates the revocation of the entire will;</span
  ><span class="akn-p" id="chp_3__sec_4__p_5" data-eId="chp_3__sec_4__p_5"
    ><span class="akn-remark" data-status="editorial"
      >[definition of "deletion" inserted by section 2(b) of <a
        data-href="/akn/za/act/1992/43"
        class="akn-ref"
        href="http://localhost:8000/resolver/resolve/akn/za/act/1992/43"
        >Act 43 of 1992</a
      >]</span
    ></span
  ></span
>
            """
        )

        self.assertMultiLineEqual(
            """
            <span class="akn-content"><span class="akn-p" data-eid="chp_3__sec_4__p_1" id="chp_3__sec_4__p_1">In this Act, unless the context otherwise indicates&#x2014;</span><span class="akn-p" data-refersto="#term-Court" data-eid="chp_3__sec_4__p_2" id="chp_3__sec_4__p_2">"<span class="akn-def" data-refersto="#term-Court">Court</span>" means a provincial or local division of the Supreme Court of South Africa or any judge thereof;</span><span class="ins akn-p" data-eid="chp_3__sec_4__p_3" id="chp_3__sec_4__p_3"><span class="akn-remark" data-status="editorial">[definition of "court" amended by <a data-href="/akn/za/act/1996/49" class="akn-ref" href="http://localhost:8000/resolver/resolve/akn/za/act/1996/49">Act 49 of 1996</a>]</span></span><span class="akn-p" data-refersto="#term-deletion" data-eid="chp_3__sec_4__p_4" id="chp_3__sec_4__p_4">"<span class="akn-def" data-refersto="#term-deletion">deletion</span>" means a deletion, cancellation or obliteration in whatever manner effected, excluding a deletion, cancellation or obliteration that contemplates the revocation of the entire will;</span><span class="akn-p" data-eid="chp_3__sec_4__p_5" id="chp_3__sec_4__p_5"><span class="akn-remark" data-status="editorial">[definition of "deletion" inserted by section 2(b) of <a data-href="/akn/za/act/1992/43" class="akn-ref" href="http://localhost:8000/resolver/resolve/akn/za/act/1992/43">Act 43 of 1992</a>]</span></span></span>
            """.strip(),
            diff.strip()
        )
