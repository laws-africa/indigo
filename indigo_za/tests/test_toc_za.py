# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase

from indigo.analysis.toc.base import descend_toc_pre_order
from indigo_api.tests.fixtures import *  # noqa
from indigo_za.toc import TOCBuilderZA
from indigo_api.models import Document, Work, Language


class TOCBuilderZATestCase(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work']

    def setUp(self):
        self.toc = TOCBuilderZA()
        self.work = Work.objects.get(id=1)
        self.eng = Language.for_code('eng')
        self.maxDiff = None

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
                'component': 'main', 'subcomponent': 'section/1', 'title': '1. Foo',
                'basic_unit': True, 'children': [],
             },
            {'id': 'chapter-1', 'num': '1.', 'type': 'chapter', 'heading': 'The Chapter',
                'component': 'main', 'subcomponent': 'chapter/1', 'title': 'Chapter 1. – The Chapter', 'basic_unit': False, 'children': [
                    {'id': 'part-A', 'num': 'A', 'type': 'part', 'heading': 'The Part',
                     'component': 'main', 'subcomponent': 'chapter/1/part/A', 'title': 'Part A – The Part', 'basic_unit': False, 'children': [
                         {'id': 'section-2', 'num': '2.', 'type': 'section', 'heading': 'Other',
                          'component': 'main', 'subcomponent': 'section/2', 'title': '2. Other', 'basic_unit': True, 'children': []},
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
                'component': 'main', 'subcomponent': 'section/1', 'title': '1. Foo', 'basic_unit': True, 'children': []},
            {'id': 'chapter-1', 'num': '1.', 'type': 'chapter', 'heading': 'The Chapter',
                'component': 'main', 'subcomponent': 'chapter/1', 'title': 'Hoofstuk 1. – The Chapter', 'basic_unit': False, 'children': [
                    {'id': 'part-A', 'num': 'A', 'type': 'part', 'heading': 'The Part',
                     'component': 'main', 'subcomponent': 'chapter/1/part/A', 'title': 'Deel A – The Part', 'basic_unit': False, 'children': [
                         {'id': 'section-2', 'num': '2.', 'type': 'section', 'heading': 'Other',
                          'component': 'main', 'subcomponent': 'section/2', 'title': '2. Other', 'basic_unit': True, 'children': []},
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
        <heading>A Title</heading>
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
        <heading>Schedule 2</heading>
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
            'type': 'attachment',
            'subcomponent': None,
            'id': 'att_1',
            'heading': 'A Title',
            'title': 'A Title',
            'basic_unit': False,
            'num': None,
            'children': [{
                'component': 'schedule1',
                'type': 'section',
                'id': 'sec_1',
                'subcomponent': 'section',
                'title': 'Section',
                'basic_unit': True,
                'children': [],
                'num': None,
                'heading': None,
            }]
        }, {
            'component': 'schedule2',
            'type': 'attachment',
            'subcomponent': None,
            'id': 'att_2',
            'heading': 'Schedule 2',
            'title': 'Schedule 2',
            'basic_unit': False,
            'num': None,
            'children': [{
                'component': 'schedule2',
                'type': 'section',
                'id': 'sec_1',
                'subcomponent': 'section',
                'title': 'Section',
                'basic_unit': True,
                'children': [],
                'num': None,
                'heading': None,
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
            {'type': 'coverpage', 'component': 'main', 'subcomponent': 'coverpage', 'title': 'Coverpage',
             'basic_unit': False, 'children': [], 'num': None, 'id': None, 'heading': None},
            {'type': 'preface', 'component': 'main', 'subcomponent': 'preface', 'title': 'Preface',
             'basic_unit': False, 'children': [], 'num': None, 'id': None, 'heading': None},
            {'type': 'preamble', 'component': 'main', 'subcomponent': 'preamble', 'title': 'Preamble',
             'basic_unit': False, 'children': [], 'num': None, 'id': None, 'heading': None},
            {'type': 'conclusions', 'component': 'main', 'subcomponent': 'conclusions', 'title': 'Conclusions',
             'basic_unit': False, 'children': [], 'num': None, 'id': None, 'heading': None},
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
            {'type': 'subpart', 'component': 'main', 'subcomponent': 'subpart', 'title': 'My subpart', 'heading': 'My subpart', 'id': 'subpart_1', 'basic_unit': False, 'children': [], 'num': None},
        ], toc)

    def test_toc_below_section(self):
        doc = Document(
            work=self.work,
            document_xml=document_fixture(xml="""
<chapter eId="chp_II">
  <num>II</num>
  <heading>Composition and organisation of Defence Force</heading>
  <section eId="sec_2">
    <num>2.</num>
    <heading>Continued existence and composition of Defence Force</heading>
    <hcontainer eId="sec_2__hcontainer_1" name="hcontainer">
      <content>
        <blockList eId="sec_2__hcontainer_1__list_1">
          <listIntroduction>The Namibian Defence Force established by section 5 of the Defence Act, 1957 (Act <ref href="/akn/na/act/1957/44">No. 44 of 1957</ref>), continues, notwithstanding the repeal of that Act by this Act, to exist and consists of -</listIntroduction>
          <item eId="sec_2__hcontainer_1__list_1__item_a">
            <num>(a)</num>
            <blockList eId="sec_2__hcontainer_1__list_1__item_a__list_1">
              <listIntroduction>the Namibian Army;</listIntroduction>
              <item eId="sec_2__hcontainer_1__list_1__item_a__list_1__item_i">
                <num>(i)</num>
                <p>xyz;</p>
              </item>
              <item eId="sec_2__hcontainer_1__list_1__item_a__list_1__item_ii">
                <num>(ii)</num>
                <blockList eId="sec_2__hcontainer_1__list_1__item_a__list_1__item_ii__list_1">
                  <listIntroduction>abc;</listIntroduction>
                  <item eId="sec_2__hcontainer_1__list_1__item_a__list_1__item_ii__list_1__item_A">
                    <num>(A)</num>
                    <p>123;</p>
                  </item>
                  <item eId="sec_2__hcontainer_1__list_1__item_a__list_1__item_ii__list_1__item_B">
                    <num>(B)</num>
                    <p>456;</p>
                  </item>
                  <item eId="sec_2__hcontainer_1__list_1__item_a__list_1__item_ii__list_1__item_C">
                    <num>(C)</num>
                    <p>789;</p>
                  </item>
                </blockList>
              </item>
              <item eId="sec_2__hcontainer_1__list_1__item_a__list_1__item_iii">
                <num>(iii)</num>
                <p>pqr;</p>
              </item>
            </blockList>
          </item>
          <item eId="sec_2__hcontainer_1__list_1__item_b">
            <num>(b)</num>
            <p>the Namibian Air Force; and</p>
          </item>
          <item eId="sec_2__hcontainer_1__list_1__item_c">
            <num>(c)</num>
            <p>the Namibian Navy.</p>
          </item>
        </blockList>
      </content>
    </hcontainer>
  </section>
  <section eId="sec_4">
    <num>4.</num>
    <heading>Executive command and functions and removal of Chief of the Defence Force</heading>
    <subsection eId="sec_4__subsec_1">
      <num>(1)</num>
      <content>
        <p>The executive command of the Defence Force is, subject to this Act, vested in the Chief of the Defence Force.</p>
      </content>
    </subsection>
    <subsection eId="sec_4__subsec_4">
      <num>(4)</num>
      <content>
        <blockList eId="sec_4__subsec_4__list_1">
          <listIntroduction>The Chief of the Defence Force ceases to hold office if the Chief of the Defence Force -</listIntroduction>
          <item eId="sec_4__subsec_4__list_1__item_a">
            <num>(a)</num>
            <p>is, subject to subsections (5) and (8), removed from office by the President pursuant to Article 120 of the Namibian Constitution; or</p>
          </item>
          <item eId="sec_4__subsec_4__list_1__item_b">
            <num>(b)</num>
            <p>resigns as Chief of the Defence Force by notice in writing addressed and delivered to the President.</p>
          </item>
        </blockList>
      </content>
    </subsection>
    <subsection eId="sec_4__subsec_6">
      <num>(6)</num>
      <content>
        <blockList eId="sec_4__subsec_6__list_1">
          <listIntroduction>On receipt of the President’s request for its recommendation referred to in subsection (5), the Security Commission -</listIntroduction>
          <item eId="sec_4__subsec_6__list_1__item_a">
            <num>(a)</num>
            <blockList eId="sec_4__subsec_6__list_1__item_a__list_1">
              <listIntroduction>must -</listIntroduction>
              <item eId="sec_4__subsec_6__list_1__item_a__list_1__item_i">
                <num>(i)</num>
                <p>in writing notify the Chief of the Defence Force of the grounds on which it is considered the Chief of the Defence Force ought to be removed from office; and</p>
              </item>
              <item eId="sec_4__subsec_6__list_1__item_a__list_1__item_ii">
                <num>(ii)</num>
                <p>afford the Chief of the Defence Force an opportunity to make oral or written representations on the matter to that Commission; and</p>
              </item>
            </blockList>
          </item>
          <item eId="sec_4__subsec_6__list_1__item_b">
            <num>(b)</num>
            <p>must thereupon, having due regard to any oral or written representations made to it by the Chief of the Defence Force, make such a recommendation and submit that recommendation together with such written representations (if any) to the President.</p>
          </item>
        </blockList>
      </content>
    </subsection>
  </section>
</chapter>
<division eId="dvs_nn_4">
  <heading>Considerations for future work</heading>
  <paragraph eId="dvs_nn_4__para_25">
    <num>25.</num>
    <content>
      <p eId="dvs_nn_4__para_25__p_1"><i>Recognizing</i> that invasive alien species are one of the main drivers of biodiversity loss, and that their increasing impact on biodiversity and economic sectors has a negative effect on human well-being, <i>emphasizes</i> the need to continue to work on this issue, in order to achieve Aichi Biodiversity Target 9;</p>
    </content>
  </paragraph>
  <paragraph eId="dvs_nn_4__para_26">
    <num>26.</num>
    <intro>
      <p eId="dvs_nn_4__para_26__intro__p_1"><i>Requests</i> the Executive Secretary, in collaboration with relevant partners, to:</p>
    </intro>
    <subparagraph eId="dvs_nn_4__para_26__subpara_a">
      <num>(a)</num>
      <intro>
        <p eId="dvs_nn_4__para_26__subpara_a__intro__p_1">Assess progress in implementing decisions of the Conference of the Parties on invasive alien species, including decisions that address gaps and inconsistencies in the international regulatory framework as identified in decision VIII/27;</p>
      </intro>
      <subparagraph eId="dvs_nn_4__para_26__subpara_a__subpara_i">
        <num>(i)</num>
        <content>
          <p eId="dvs_nn_4__para_26__subpara_a__subpara_i__p_1">xyz;</p>
        </content>
      </subparagraph>
      <subparagraph eId="dvs_nn_4__para_26__subpara_a__subpara_ii">
        <num>(ii)</num>
        <content>
          <p eId="dvs_nn_4__para_26__subpara_a__subpara_ii__p_1">abc;</p>
        </content>
      </subparagraph>
      <subparagraph eId="dvs_nn_4__para_26__subpara_a__subpara_iii">
        <num>(iii)</num>
        <content>
          <p eId="dvs_nn_4__para_26__subpara_a__subpara_iii__p_1">pqr;</p>
        </content>
      </subparagraph>
    </subparagraph>
    <subparagraph eId="dvs_nn_4__para_26__subpara_b">
      <num>(b)</num>
      <content>
        <p eId="dvs_nn_4__para_26__subpara_b__p_1">Prepare a preliminary list of the most common pathways for the introduction of invasive alien species, propose criteria for use at regional and subregional levels or other ways by which they may be prioritized, and identify a range of tools that may be used to manage or minimize the risks associated with these pathways; and to report thereon to a meeting of the Subsidiary Body on Scientific, Technical and Technological Advice before the twelfth meeting of the Conference of the Parties, in order to inform consideration of the need for future work.</p>
      </content>
    </subparagraph>
    <wrapUp>
      <block name="quote" eId="dvs_nn_4__para_26__wrapup__block_1"><embeddedStructure startQuote="“" eId="dvs_nn_4__para_26__wrapup__block_1__embeddedStructure_1"><subparagraph eId="dvs_nn_4__para_26__wrapup__block_1__embeddedStructure_1__subpara_a"><num>(a)</num><intro><p eId="dvs_nn_4__para_26__wrapup__block_1__embeddedStructure_1__subpara_a__intro__p_1">Assess progress in implementing decisions of the Conference of the Parties on invasive alien species, including decisions that address gaps and inconsistencies in the international regulatory framework as identified in decision VIII/27;</p></intro><subparagraph eId="dvs_nn_4__para_26__wrapup__block_1__embeddedStructure_1__subpara_a__subpara_i"><num>(i)</num><content><p eId="dvs_nn_4__para_26__wrapup__block_1__embeddedStructure_1__subpara_a__subpara_i__p_1">xyz;</p></content></subparagraph><subparagraph eId="dvs_nn_4__para_26__wrapup__block_1__embeddedStructure_1__subpara_a__subpara_ii"><num>(ii)</num><content><p eId="dvs_nn_4__para_26__wrapup__block_1__embeddedStructure_1__subpara_a__subpara_ii__p_1">abc;</p></content></subparagraph><subparagraph eId="dvs_nn_4__para_26__wrapup__block_1__embeddedStructure_1__subpara_a__subpara_iii"><num>(iii)</num><content><p eId="dvs_nn_4__para_26__wrapup__block_1__embeddedStructure_1__subpara_a__subpara_iii__p_1">pqr;</p></content></subparagraph></subparagraph></embeddedStructure></block>
    </wrapUp>
  </paragraph>
</division>"""),
            language=self.eng)

        toc = self.toc.table_of_contents_for_document(doc)
        toc_elements = list(descend_toc_pre_order(toc))
        self.assertEqual(len(toc_elements), 29)
        self.assertEqual(
            ['chp_II', 'sec_2', 'sec_2__hcontainer_1__list_1__item_a',
             'sec_2__hcontainer_1__list_1__item_a__list_1__item_i',
             'sec_2__hcontainer_1__list_1__item_a__list_1__item_ii',
             'sec_2__hcontainer_1__list_1__item_a__list_1__item_ii__list_1__item_A',
             'sec_2__hcontainer_1__list_1__item_a__list_1__item_ii__list_1__item_B',
             'sec_2__hcontainer_1__list_1__item_a__list_1__item_ii__list_1__item_C',
             'sec_2__hcontainer_1__list_1__item_a__list_1__item_iii',
             'sec_2__hcontainer_1__list_1__item_b',
             'sec_2__hcontainer_1__list_1__item_c',
             'sec_4', 'sec_4__subsec_1', 'sec_4__subsec_4',
             'sec_4__subsec_4__list_1__item_a',
             'sec_4__subsec_4__list_1__item_b',
             'sec_4__subsec_6',
             'sec_4__subsec_6__list_1__item_a',
             'sec_4__subsec_6__list_1__item_a__list_1__item_i',
             'sec_4__subsec_6__list_1__item_a__list_1__item_ii',
             'sec_4__subsec_6__list_1__item_b',
             'dvs_nn_4',
             'dvs_nn_4__para_25', 'dvs_nn_4__para_26',
             'dvs_nn_4__para_26__subpara_a',
             'dvs_nn_4__para_26__subpara_a__subpara_i',
             'dvs_nn_4__para_26__subpara_a__subpara_ii',
             'dvs_nn_4__para_26__subpara_a__subpara_iii',
             'dvs_nn_4__para_26__subpara_b'],
            [t.id for t in toc_elements]
        )
