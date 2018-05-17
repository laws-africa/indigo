# -*- coding: utf-8 -*-

from nose.tools import *  # noqa

from django.test import testcases
from indigo_api.importers.pl import ImporterPL

class ImporterPLTestCase(testcases.TestCase):
    def setUp(self):
        self.importer = ImporterPL()

    def test_reformat_text_simple(self):
        text = u"All your base are belong \n to Legia Warszawa FC."
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, "All your base are belong   to Legia Warszawa FC.")

    def test_reformat_text_remove_hyphenation(self):
        text = u"All your base are be-\nlong to Legia Warszawa FC."
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, "All your base are belong to Legia Warszawa FC.")
        
    def test_reformat_text_keep_linebreak_on_divisions(self):
        text = (u"DZIAŁ VIII All your base are belong to Legia Warszawa FC.\n"
                u"DZIAŁ IX The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)        

    def test_reformat_text_keep_linebreak_on_chapters(self):
        text = (u"Rozdział 1 All your base are belong to Legia Warszawa FC.\n"
                u"Rozdział 2 The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_articles(self):
        text = (u"Art. 1 All your base are belong to Legia Warszawa FC.\n"
                u"Art. 2 The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_paragraphs(self):
        text = (u"1. All your base are belong to Legia Warszawa FC.\n"
                u"2. The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)
        
    def test_reformat_text_keep_linebreak_on_paragraphs_section_sign(self):
        text = (u"§ 1. All your base are belong to Legia Warszawa FC.\n"
                u"§ 2. The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_points(self):
        text = (u"1) All your base are belong to Legia Warszawa FC.\n"
                u"2) The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_letters(self):
        text = (u"a) All your base are belong to Legia Warszawa FC.\n"
                u"b) The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_tirets(self):
        text = (u"– All your base are belong to Legia Warszawa FC.\n"
                u"– The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_on_double_tirets(self):
        text = (u"– – All your base are belong to Legia Warszawa FC.\n"
                u"– – The right to consume sausages shall not be abrogated.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)

    def test_reformat_text_keep_linebreak_complex(self):
        text = (u"Art. 1ab. Some law.\n"
                u"2cd. Some law.\n"
                u"§ 3ef. Some law.\n"
                u"3gh) Some law.\n"
                u"ij) Some law.\n"
                u"– Some law.")
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, text)
