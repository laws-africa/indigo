# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase

from indigo_api.tests.fixtures import *  # noqa
from indigo_za.toc import TOCBuilderZA
from indigo_api.models import Document, Work, Language


class TOCBuilderZATestCase(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work']

    def setUp(self):
        self.toc = TOCBuilderZA()
        self.work = Work.objects.get(id=1)

    def test_table_of_contents(self):
        d = Document()
        d.work = self.work
        d.content = document_fixture(xml="""
        <body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
          <section eId="section-1">
            <num>1.</num>
            <heading>Foo</heading>
            <content>
              <p>hello</p>
            </content>
          </section>
          <chapter eId="chapter-1">
            <num>1.</num>
            <heading>The Chapter</heading>
            <part eId="part-A">
              <num>A</num>
              <heading>The Part</heading>
              <section eId="section-2">
                <num>2.</num>
                <heading>Other</heading>
                <content>
                  <p>hi</p>
                </content>
              </section>
            </part>
          </chapter>
        </body>
        """)
        d.language = Language.objects.get(language__pk='en')
        toc = d.table_of_contents()
        toc = [t.as_dict() for t in toc]
        self.maxDiff = None
        self.assertEqual(toc, [
            {'id': 'section-1', 'num': '1.', 'type': 'section', 'heading': 'Foo',
                'component': 'main', 'subcomponent': 'section/1', 'title': '1. Foo'},
            {'id': 'chapter-1', 'num': '1.', 'type': 'chapter', 'heading': 'The Chapter',
                'component': 'main', 'subcomponent': 'chapter/1', 'title': 'Chapter 1. – The Chapter', 'children': [
                    {'id': 'part-A', 'num': 'A', 'type': 'part', 'heading': 'The Part',
                     'component': 'main', 'subcomponent': 'chapter/1/part/A', 'title': 'Part A – The Part', 'children': [
                         {'id': 'section-2', 'num': '2.', 'type': 'section', 'heading': 'Other',
                          'component': 'main', 'subcomponent': 'section/2', 'title': '2. Other'},
                     ]
                     },
                ]},
        ])

    def test_table_of_contents_afr(self):
        d = Document()
        d.work = self.work
        d.content = document_fixture(xml="""
        <body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
          <section eId="section-1">
            <num>1.</num>
            <heading>Foo</heading>
            <content>
              <p>hello</p>
            </content>
          </section>
          <chapter eId="chapter-1">
            <num>1.</num>
            <heading>The Chapter</heading>
            <part eId="part-A">
              <num>A</num>
              <heading>The Part</heading>
              <section eId="section-2">
                <num>2.</num>
                <heading>Other</heading>
                <content>
                  <p>hi</p>
                </content>
              </section>
            </part>
          </chapter>
        </body>
        """)
        d.language = Language.objects.get(language__pk='af')

        toc = d.table_of_contents()
        toc = [t.as_dict() for t in toc]
        self.maxDiff = None
        self.assertEqual(toc, [
            {'id': 'section-1', 'num': '1.', 'type': 'section', 'heading': 'Foo',
                'component': 'main', 'subcomponent': 'section/1', 'title': '1. Foo'},
            {'id': 'chapter-1', 'num': '1.', 'type': 'chapter', 'heading': 'The Chapter',
                'component': 'main', 'subcomponent': 'chapter/1', 'title': 'Hoofstuk 1. – The Chapter', 'children': [
                    {'id': 'part-A', 'num': 'A', 'type': 'part', 'heading': 'The Part',
                     'component': 'main', 'subcomponent': 'chapter/1/part/A', 'title': 'Deel A – The Part', 'children': [
                         {'id': 'section-2', 'num': '2.', 'type': 'section', 'heading': 'Other',
                          'component': 'main', 'subcomponent': 'section/2', 'title': '2. Other'},
                     ]
                     },
                ]},
        ])

    def test_component_table_of_contents(self):
        d = Document()
        d.work = self.work
        d.content = """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="singleVersion">
    <meta>
      <identification source="#openbylaws">
        <FRBRWork>
          <FRBRthis value="/za/by-law/cape-town/2002/community-fire-safety/!main"/>
          <FRBRuri value="/za/by-law/cape-town/2002/community-fire-safety"/>
          <FRBRalias value="Community Fire Safety By-law"/>
          <FRBRdate date="2002-02-28" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/za/by-law/cape-town/2002/community-fire-safety/main/eng@"/>
          <FRBRuri value="/za/by-law/cape-town/2002/community-fire-safety/eng@"/>
          <FRBRdate date="2002-02-28" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/za/by-law/cape-town/2002/community-fire-safety/main/eng@"/>
          <FRBRuri value="/za/by-law/cape-town/2002/community-fire-safety/eng@"/>
          <FRBRdate date="2014-01-14" name="Generation"/>
          <FRBRauthor href="#openbylaws" as="#author"/>
        </FRBRManifestation>
      </identification>
    </meta>
    <body></body>
    <attachments>
      <attachment eId="att_1">
        <doc name="schedule">
          <meta>
            <identification source="#slaw">
              <FRBRWork>
                <FRBRthis value="/za/act/1980/01/!schedule1"/>
                <FRBRuri value="/za/act/1980/01"/>
                <FRBRalias value="A Title"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council" as="#author"/>
                <FRBRcountry value="za"/>
              </FRBRWork>
              <FRBRExpression>
                <FRBRthis value="/za/act/1980/01/eng@/schedule1"/>
                <FRBRuri value="/za/act/1980/01/eng@"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council" as="#author"/>
                <FRBRlanguage language="eng"/>
              </FRBRExpression>
              <FRBRManifestation>
                <FRBRthis value="/za/act/1980/01/eng@/schedule1"/>
                <FRBRuri value="/za/act/1980/01/eng@"/>
                <FRBRdate date="2015-04-22" name="Generation"/>
                <FRBRauthor href="#slaw" as="#author"/>
              </FRBRManifestation>
            </identification>
          </meta>
          <mainBody>
            <section eId="sec_1">
              <content>
                <p>1. Foo</p>
                <p>2. Bar</p>
              </content>
            </section>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_2">
        <doc name="schedule">
          <meta>
            <identification source="#slaw">
              <FRBRWork>
                <FRBRthis value="/za/act/1980/01/!schedule2"/>
                <FRBRuri value="/za/act/1980/01"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council" as="#author"/>
                <FRBRcountry value="za"/>
              </FRBRWork>
              <FRBRExpression>
                <FRBRthis value="/za/act/1980/01/eng@/schedule2"/>
                <FRBRuri value="/za/act/1980/01/eng@"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council" as="#author"/>
                <FRBRlanguage language="eng"/>
              </FRBRExpression>
              <FRBRManifestation>
                <FRBRthis value="/za/act/1980/01/eng@/schedule2"/>
                <FRBRuri value="/za/act/1980/01/eng@"/>
                <FRBRdate date="2015-04-22" name="Generation"/>
                <FRBRauthor href="#slaw" as="#author"/>
              </FRBRManifestation>
            </identification>
          </meta>
          <mainBody>
            <section eId="sec_1">
              <content>
                <p>Baz</p>
                <p>Boom</p>
              </content>
            </section>
          </mainBody>
        </doc>
      </attachment>
    </attachments>
  </act>
</akomaNtoso>
        """
        d.language = Language.objects.get(language__pk='en')
        toc = d.table_of_contents()
        toc = [t.as_dict() for t in toc]
        self.maxDiff = None
        self.assertEqual([{
            'component': 'schedule1',
            'type': 'doc',
            'subcomponent': None,
            'heading': 'A Title',
            'title': 'A Title',
             'children': [{
                 'component': 'schedule1',
                 'type': 'section',
                 'id': 'sec_1',
                 'subcomponent': 'section',
                 'title': 'Section',
             }]
        }, {
            'component': 'schedule2',
            'type': 'doc',
            'subcomponent': None,
            'heading': 'Schedule 2',
            'title': 'Schedule 2',
            'children': [{
                'component': 'schedule2',
                'type': 'section',
                'id': 'sec_1',
                'subcomponent': 'section',
                'title': 'Section'
            }]
        }], toc)

    def test_preamble_and_friends_in_table_of_contents(self):
        d = Document()
        d.work = self.work
        d.content = document_fixture(xml="""
        <coverpage>
            <content><p>hi</p></content>
        </coverpage>
        <preface>
            <content><p>hi</p></content>
        </preface>
        <preamble>
            <content><p>hi</p></content>
        </preamble>
        <body>
            <content><p>hi</p></content>
        </body>
        <conclusions>
            <content><p>hi></p></content>
        </conclusions>
        """)
        d.language = Language.objects.get(language__pk='en')

        toc = d.table_of_contents()
        toc = [t.as_dict() for t in toc]
        self.maxDiff = None
        self.assertEqual(toc, [
            {'type': 'coverpage', 'component': 'main', 'subcomponent': 'coverpage', 'title': 'Coverpage'},
            {'type': 'preface', 'component': 'main', 'subcomponent': 'preface', 'title': 'Preface'},
            {'type': 'preamble', 'component': 'main', 'subcomponent': 'preamble', 'title': 'Preamble'},
            {'type': 'conclusions', 'component': 'main', 'subcomponent': 'conclusions', 'title': 'Conclusions'},
        ])

    def test_subpart_without_number(self):
        d = Document()
        d.work = self.work
        d.content = document_fixture(xml="""
        <body>
          <subpart eId="subpart_1">
            <heading>My subpart</heading>
          </subpart>
        </body>
        """)
        d.language = Language.objects.get(language__pk='en')

        toc = d.table_of_contents()
        toc = [t.as_dict() for t in toc]
        self.maxDiff = None
        self.assertEqual([
            {'type': 'subpart', 'component': 'main', 'subcomponent': 'subpart', 'title': 'My subpart', 'heading': 'My subpart', 'id': 'subpart_1'},
        ], toc)
