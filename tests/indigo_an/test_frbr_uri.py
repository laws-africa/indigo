from unittest import TestCase
from nose.tools import *

from indigo_an.frbr_uri import FrbrUri

class FrbrUriTestCase(TestCase):
    def test_bad_value(self):
        assert_raises(ValueError, FrbrUri.parse, "/badness")

    def test_simple(self):
        uri = FrbrUri.parse("/za/act/1980/01")
        assert_equal(uri.country, "za")
        assert_equal(uri.doctype, "act")
        assert_equal(uri.subtype, None)
        assert_equal(uri.actor, None)
        assert_equal(uri.date, "1980")
        assert_equal(uri.number, "01")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)

        assert_equal("/za/act/1980/01", uri.work_uri())

    def test_with_subtype(self):
        uri = FrbrUri.parse("/za/act/by-law/1980/01")
        assert_equal(uri.country, "za")
        assert_equal(uri.doctype, "act")
        assert_equal(uri.subtype, "by-law")
        assert_equal(uri.actor, None)
        assert_equal(uri.date, "1980")
        assert_equal(uri.number, "01")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)

        assert_equal("/za/act/by-law/1980/01", uri.work_uri())

    def test_with_subtype_and_actor(self):
        uri = FrbrUri.parse("/za/act/by-law/actor/1980/01")
        assert_equal(uri.country, "za")
        assert_equal(uri.doctype, "act")
        assert_equal(uri.subtype, "by-law")
        assert_equal(uri.actor, "actor")
        assert_equal(uri.date, "1980")
        assert_equal(uri.number, "01")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)

        assert_equal("/za/act/by-law/actor/1980/01", uri.work_uri())

    def test_with_long_date(self):
        uri = FrbrUri.parse("/za/act/1980-02-01/01")
        assert_equal(uri.country, "za")
        assert_equal(uri.doctype, "act")
        assert_equal(uri.subtype, None)
        assert_equal(uri.actor, None)
        assert_equal(uri.date, "1980-02-01")
        assert_equal(uri.number, "01")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)

        assert_equal("/za/act/1980-02-01/01", uri.work_uri())

    def test_with_non_numeric_number(self):
        uri = FrbrUri.parse("/za/act/1980/nn")
        assert_equal(uri.country, "za")
        assert_equal(uri.doctype, "act")
        assert_equal(uri.subtype, None)
        assert_equal(uri.actor, None)
        assert_equal(uri.date, "1980")
        assert_equal(uri.number, "nn")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)

        assert_equal("/za/act/1980/nn", uri.work_uri())

    def test_expression_uri(self):
        uri = FrbrUri.parse("/za/act/1980/nn")
        uri.language = "eng"

        assert_equal("/za/act/1980/nn", uri.work_uri())
        assert_equal("/za/act/1980/nn/eng@", uri.expression_uri())

