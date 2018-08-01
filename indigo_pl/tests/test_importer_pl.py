# -*- coding: utf-8 -*-

from nose.tools import *  # noqa

from django.test import testcases
from indigo_pl.importer import ImporterPL

def make_tag(text, top = 100, height = 18):
    return (u"<text top='" + str(top).encode("utf-8").decode("utf-8") + u"' left='100' height='" 
        + str(height).encode("utf-8").decode("utf-8") + u"'>" + text + u"</text>")

class ImporterPLTestCase(testcases.TestCase):

    def setUp(self):
        self.importer = ImporterPL()

    def test_reformat_text_simple(self):
        text = u"All your base are belong \n to Legia Warszawa FC."
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, "All your base are belong   to Legia Warszawa FC.")

    def test_reformat_text_remove_hyphenation(self):
        text = u"All your base are be-\nlong to Legia Warszawa FC."
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, "All your base are belong to Legia Warszawa FC.")

    def test_reformat_text_keep_linebreak_on_divisions(self):
        text = (u"DZIAŁ VIII All your base are belong to Legia Warszawa FC.\n"
                u"DZIAŁ IX The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_chapters(self):
        text = (u"Rozdział 1 All your base are belong to Legia Warszawa FC.\n"
                u"Rozdział 2 The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_articles(self):
        text = (u"Art. 1 All your base are belong to Legia Warszawa FC.\n"
                u"Art. 2 The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_paragraphs(self):
        text = (u"1. All your base are belong to Legia Warszawa FC.\n"
                u"2. The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_paragraphs_section_sign(self):
        text = (u"§ 1. All your base are belong to Legia Warszawa FC.\n"
                u"§ 2. The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_points(self):
        text = (u"1) All your base are belong to Legia Warszawa FC.\n"
                u"2) The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_letters(self):
        text = (u"a) All your base are belong to Legia Warszawa FC.\n"
                u"b) The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_tirets(self):
        text = (u"– All your base are belong to Legia Warszawa FC.\n"
                u"– The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_double_tirets(self):
        text = (u"– – All your base are belong to Legia Warszawa FC.\n"
                u"– – The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_complex(self):
        text = (u"Art. 1ab. Some law.\n"
                u"2cd. Some law.\n"
                u"§ 3ef. Some law.\n"
                u"3gh) Some law.\n"
                u"ij) Some law.\n"
                u"– Some law.")
        reformatted = self.importer.reformat_text(make_tag(text))
        assert_equal(reformatted, text)
        
    def test_reformat_remove_header_footer(self):
        header_text = u"Copyright ISAP"
        text = u"All your base are belong to Legia Warszawa FC."
        footer_text = u"page 3/123"
        reformatted = self.importer.reformat_text(
            make_tag(header_text, 10) + make_tag(text) + make_tag(footer_text, 1080))
        assert_equal(reformatted, text)
        
    def test_reformat_process_superscripts(self):
        before = u"Some text "
        text1 = u"Art. 123"
        text2 = u"456"
        text3 = u". Bla bla bla "
        after = u"Some other text"
        reformatted = self.importer.reformat_text(""
            + make_tag(before, 90, 18) # Previous line.
            + make_tag(text1, 100, 18)
            + make_tag(text2, 99, 12) # Note lower "top" and "height" attributes
            + make_tag(text3, 100, 18)
            + make_tag(after, 110, 18)) # Following line.
        assert_equal(reformatted, before + text1 + ImporterPL.SUPERSCRIPT_START + text2 
                     + ImporterPL.SUPERSCRIPT_END + text3 + after)

    def test_reformat_remove_footnotes(self):
        text1 = u"The right "
        text2 = u"to consume "
        text3 = u"sausage "
        text4 = u"shall not "
        text5 = u"be abrogated "
        footnote = u"As promulgated by the Sausage Act of 1 April 1234"
        reformatted = self.importer.reformat_text(""
            + make_tag(text1, 100, 18)
            + make_tag(text2, 110, 18)
            + make_tag(text3, 120, 18)
            + make_tag(text4, 130, 18)
            + make_tag(text5, 140, 18)
            + make_tag(footnote, 150, 12)) # Note lower "height" attribute.
        assert_equal(reformatted, text1 + text2 + text3 + text4 + text5)
