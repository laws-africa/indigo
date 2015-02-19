from unittest import TestCase
from nose.tools import *
from datetime import date

from indigo_an.act import Act, datestring

class ActTestCase(TestCase):
    def test_empty_act(self):
        a = Act()
        assert_equal(a.title, "Untitled")
        assert_is_not_none(a.meta)
        assert_is_not_none(a.body)

    def test_frbr_uri(self):
        a = Act()
        a.frbr_uri = '/za/act/2007/01'
        assert_equal(a.frbr_uri, '/za/act/2007/01/')
        assert_equal(a.meta.identification.FRBRExpression.FRBRuri.get('value'), '/za/act/2007/01/eng@')
        assert_equal(a.meta.identification.FRBRManifestation.FRBRuri.get('value'), '/za/act/2007/01/eng@')
        
        assert_equal(a.number, '01')

    def test_empty_body(self):
        a = Act()
        assert_not_equal(a.body_xml, '')
        a.body_xml = ''
        assert_not_equal(a.body_xml, '')

    def test_work_date(self):
        a = Act()
        a.work_date = '2012-01-02'
        assert_equal(datestring(a.work_date), '2012-01-02')
        assert_is_instance(a.work_date, date)

    def test_expression_date(self):
        a = Act()
        a.expression_date = '2012-01-02'
        assert_equal(datestring(a.expression_date), '2012-01-02')
        assert_is_instance(a.expression_date, date)

    def test_manifestation_date(self):
        a = Act()
        a.manifestation_date = '2012-01-02'
        assert_equal(datestring(a.manifestation_date), '2012-01-02')
        assert_is_instance(a.manifestation_date, date)

    def test_publication_date(self):
        a = Act()
        assert_is_none(a.publication_date)

        a.publication_date = '2012-01-02'
        assert_equal(datestring(a.publication_date), '2012-01-02')
        assert_is_instance(a.publication_date, date)

    def test_publication_number(self):
        a = Act()
        assert_is_none(a.publication_number)

        a.publication_number = '1234'
        assert_equal(a.publication_number, '1234')

    def test_publication_name(self):
        a = Act()
        assert_is_none(a.publication_name)

        a.publication_name = 'Publication'
        assert_equal(a.publication_name, 'Publication')
