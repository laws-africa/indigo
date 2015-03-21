from unittest import TestCase
from nose.tools import *

from cobalt.uri import FrbrUri

class FrbrUriTestCase(TestCase):
    def test_bad_value(self):
        assert_raises(ValueError, FrbrUri.parse, "/badness")

    def test_simple(self):
        uri = FrbrUri.parse("/za/act/1980/01")
        assert_equal(uri.country, "za")
        assert_equal(uri.locality, None)
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
        assert_equal(uri.locality, None)
        assert_equal(uri.doctype, "act")
        assert_equal(uri.subtype, "by-law")
        assert_equal(uri.actor, None)
        assert_equal(uri.date, "1980")
        assert_equal(uri.number, "01")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)

        assert_equal("/za/act/by-law/1980/01", uri.work_uri())

    def test_with_locality(self):
        uri = FrbrUri.parse("/za-cpt/act/by-law/1980/01")
        assert_equal(uri.country, "za")
        assert_equal(uri.locality, "cpt")
        assert_equal(uri.doctype, "act")
        assert_equal(uri.subtype, "by-law")
        assert_equal(uri.actor, None)
        assert_equal(uri.date, "1980")
        assert_equal(uri.number, "01")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)

        assert_equal("/za-cpt/act/by-law/1980/01", uri.work_uri())

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

    def test_parse_expression(self):
        uri = FrbrUri.parse("/za/act/1980/02/eng@")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, '')

        uri = FrbrUri.parse("/za/act/1980/02/eng@2014-01-01")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, "2014-01-01")

    def test_parse_expression_component(self):
        uri = FrbrUri.parse("/za/act/1980/02/eng/main")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)
        assert_equal(uri.expression_component, "main")

        uri = FrbrUri.parse("/za/act/1980/02/eng/main/schedule1")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)
        assert_equal(uri.expression_component, "main/schedule1")

        uri = FrbrUri.parse("/za/act/1980/02/eng@/main/schedule1")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, '')
        assert_equal(uri.expression_component, "main/schedule1")

        uri = FrbrUri.parse("/za/act/1980/02/eng@2014-01-01/main/schedule1")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, "2014-01-01")
        assert_equal(uri.expression_component, "main/schedule1")

        uri = FrbrUri.parse("/za/act/1980/02/eng@2014-01-01/main/schedule1")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, "2014-01-01")
        assert_equal(uri.expression_component, "main/schedule1")

    def test_parse_expression_date(self):
        # A dangling @ indicates the very FIRST expression date, which
        # we represent with an empty string (''). 
        # A URI without an @ at all, indicates the most recent
        # expression date, which is None.

        uri = FrbrUri.parse("/za/act/1980/02/eng")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)
        assert_equal(uri.expression_uri(), '/za/act/1980/02/eng')

        uri = FrbrUri.parse("/za/act/1980/02/eng/main")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, None)

        uri = FrbrUri.parse("/za/act/1980/02/eng@")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, '')
        assert_equal(uri.expression_uri(), '/za/act/1980/02/eng@')

        uri = FrbrUri.parse("/za/act/1980/02/eng@/main")
        assert_equal(uri.language, "eng")
        assert_equal(uri.expression_date, '')

    def test_expression_uri(self):
        uri = FrbrUri.parse("/za/act/1980/02/eng")
        uri.expression_date = '2014-01-01'
        uri.expression_component = 'main'
        uri.format = 'html'

        assert_equal("/za/act/1980/02/eng@2014-01-01/main", uri.expression_uri())

    def test_manifestation_uri(self):
        uri = FrbrUri.parse("/za/act/1980/02/eng")
        uri.expression_date = '2014-01-01'
        uri.expression_component = 'main'
        uri.format = 'html'

        assert_equal("/za/act/1980/02/eng@2014-01-01/main.html", uri.manifestation_uri())
