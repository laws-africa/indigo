# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from indigo_api.models import Document
from indigo_api.tests.fixtures import *  # noqa


class AnalysisTestCase(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'work', 'published']

    def setUp(self):
        self.client.default_format = 'json'
        assert_true(self.client.login(username='email@example.com', password='password'))

    def test_link_terms_no_input(self):
        response = self.client.post('/api/documents/1/analysis/link-terms', {
            'document': {},
        })
        assert_equal(response.status_code, 400)

    def test_link_terms(self):
        response = self.client.post('/api/documents/1/analysis/link-terms', {
            'document': {
                'frbr_uri': '/za/act/1992/1',
                'expression_date': '2001-01-01',
                'language': 'eng',
                'content': document_fixture(xml="""
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

    def test_link_terms_no_perms(self):
        self.client.logout()
        self.assertTrue(self.client.login(username='no-perms@example.com', password='password'))
        user = User.objects.get(username='no-perms@example.com')

        data = {
            'document': {
                'frbr_uri': '/za/act/1992/1',
                'expression_date': '2001-01-01',
                'language': 'eng',
                'content': document_fixture(xml="""
<section id="section-1">
  <num>1.</num>
  <heading>Definitions and interpretation</heading>
  <content>
    <p>test</p>
  </content>
</section>
""")
            }
        }

        # user doesn't have perms
        response = self.client.post('/api/documents/1/analysis/link-terms', data)
        self.assertEqual(response.status_code, 403)

        # user has view perms, but not change
        user.user_permissions.add(Permission.objects.get(
            codename='view_document',
            content_type=ContentType.objects.get_for_model(Document)
        ))

        response = self.client.post('/api/documents/1/analysis/link-terms', data)
        self.assertEqual(response.status_code, 403)

        # user has both view and change perms, but not publication permissions
        user.user_permissions.add(Permission.objects.get(
            codename='change_document',
            content_type=ContentType.objects.get_for_model(Document)
        ))

        response = self.client.post('/api/documents/1/analysis/link-terms', data)
        self.assertEqual(response.status_code, 403)

        # add publish perm
        user.user_permissions.add(Permission.objects.get(
            codename='publish_document',
            content_type=ContentType.objects.get_for_model(Document)
        ))

        response = self.client.post('/api/documents/1/analysis/link-terms', data)
        self.assertEqual(response.status_code, 403)

        # add missing country permission
        user.editor.permitted_countries.add(Document.objects.get(pk=1).work.country)

        response = self.client.post('/api/documents/1/analysis/link-terms', data)
        self.assertEqual(response.status_code, 200)
