from unittest import TestCase
from nose.tools import *

from indigo_an.act import Act

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

