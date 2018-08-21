# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase

from indigo_api.tests.fixtures import *  # noqa


class AnalysisTestCase(APITestCase):
    fixtures = ['countries', 'user', 'editor', 'work']

    def setUp(self):
        self.client.default_format = 'json'
        assert_true(self.client.login(username='email@example.com', password='password'))

    def test_link_terms_no_input(self):
        response = self.client.post('/api/analysis/link-terms', {
            'document': {},
        })
        assert_equal(response.status_code, 400)

    def test_link_terms(self):
        response = self.client.post('/api/analysis/link-terms', {
            'document': {
                'expression_date': '2001-01-01',
                'language': 'eng',
                'content': document_fixture(xml=u"""
<section id="section-1">
  <num>1.</num>
  <heading>Definitions and interpretation</heading>
  <subsection id="section-1.subsection-0">
    <content>
      <p>In these By-laws, any word or expression that has been defined in the National Road Traffic Act, 1996 (Act No. 93 of 1996) has that meaning and, unless the context otherwise indicates –</p>
    </content>
  </subsection>
  <subsection id="section-1.subsection-1">
    <content>
      <blockList id="section-1.subsection-1.list1">
        <listIntroduction>"authorised official" means –</listIntroduction>
        <item id="section-1.subsection-1.list1.a">
          <num>(a)</num>
          <p>a member of the Johannesburg Metropolitan Police established in terms of section 64A of the South African Police Service Act, 1995 (Act No. 68 of 1995); or</p>
        </item>
        <item id="section-1.subsection-1.list1.b">
          <num>(b)</num>
          <p>any person or official authorised as such, in writing, by the Council;</p>
        </item>
      </blockList>
    </content>
  </subsection>
  <subsection id="section-1.subsection-2">
    <content>
      <p>"backfill" means to replace the structural layers, including the base, sub-base, sudgrade and subgrade but excluding the surfacing, in a trench dug in, or other excavation of, a road reserve, and “backfilling” is construed accordingly;</p>
    </content>
  </subsection>
  <subsection id="section-1.subsection-3">
    <content>
      <p>"these By-Laws" includes the schedules;</p>
    </content>
  </subsection>
</section>
""")
            }
        })
        assert_equal(response.status_code, 200)

        content = response.data['document']['content']

        assert_true(content.startswith('<akomaNtoso'))
        assert_in('<def ', content)
        assert_in('<TLCTerm ', content)
