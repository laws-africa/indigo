# -*- coding: utf-8 -*-
from django.test import TestCase

from indigo_api.tests.fixtures import document_fixture, component_fixture
from indigo_api.models import Document, Language, Work

from indigo.analysis.toc.base import TOCBuilderBase


def flat_toc(tocs):
    flat_toc = []

    def unpack(el):
        flat_toc.append(el)
        children = el.get('children', [])
        for child in children:
            unpack(child)

    for toc in tocs:
        unpack(toc)

    return flat_toc


class TOCBuilderBaseTestCase(TestCase):
    fixtures = ['languages_data', 'countries']

    def setUp(self):
        self.work = Work(frbr_uri='/za/act/1998/1')
        self.builder = TOCBuilderBase()
        self.eng = Language.for_code('eng')

    def test_toc_simple(self):
        doc = Document(
            work=self.work,
            document_xml=document_fixture(text="hi"),
            language=self.eng)

        toc = self.builder.table_of_contents_for_document(doc)
        self.assertEqual([t.as_dict() for t in toc], [{
            'component': 'main',
            'title': 'Section',
            'type': 'section',
            'id': 'sec_1',
            'subcomponent': 'section',
            'basic_unit': True,
            'children': [],
        }])

    def test_toc_item_simple(self):
        doc = Document(
            work=self.work,
            document_xml=document_fixture(text="hi"),
            language=self.eng)

        elem = doc.doc.root.xpath("//*[@eId='sec_1']")[0]

        toc = self.builder.table_of_contents_entry_for_element(doc, elem)
        self.assertEqual(toc.as_dict(), {
            'component': 'main',
            'title': 'Section',
            'type': 'section',
            'id': 'sec_1',
            'subcomponent': 'section',
            'basic_unit': True,
            'children': [],
        })
        self.assertEqual(toc.id, toc.qualified_id)

    def test_toc_item_in_schedule(self):
        doc = Document(
            work=self.work,
            document_xml=component_fixture(text="hi"),
            language=self.eng)

        elem = doc.doc.root.xpath("//a:attachment//*[@eId='sec_1']", namespaces={'a': doc.doc.namespace})[0]

        toc = self.builder.table_of_contents_entry_for_element(doc, elem)
        self.assertEqual(toc.as_dict(), {
            'component': 'schedule1',
            'title': 'Section',
            'type': 'section',
            'id': 'sec_1',
            'subcomponent': 'section',
            'basic_unit': True,
            'children': [],
        })
        self.assertEqual("att_1/sec_1", toc.qualified_id)

    def test_toc_with_schedule(self):
        doc = Document(
            work=self.work,
            document_xml=component_fixture(text="hi"),
            language=self.eng)

        # toc now includes `paragraph` (in main body of component fixture)
        toc = self.builder.table_of_contents_for_document(doc)
        self.assertEqual([{
            'type': 'paragraph',
            'component': 'main',
            'subcomponent': 'paragraph',
            'title': 'Paragraph',
            'basic_unit': False,
            'children': [],
        }, {
            'type': 'attachment',
            'component': 'schedule1',
            'subcomponent': None,
            'title': 'Schedule 1',
            'heading': 'Schedule 1',
            'id': 'att_1',
            'basic_unit': False,
            'children': [{
                'component': 'schedule1',
                'title': 'Section',
                'type': 'section',
                'id': 'sec_1',
                'subcomponent': 'section',
                'basic_unit': True,
                'children': [],
            }],
        }], [t.as_dict() for t in toc])
        self.assertEqual("att_1/sec_1", toc[1].children[0].qualified_id)

    def test_toc_with_schedule_no_heading(self):
        doc = Document(
            work=self.work,
            document_xml=component_fixture(text="hi"),
            language=self.eng)

        # strip the heading element, the builder will use the FRBRalias instead
        for node in doc.doc.root.xpath('//a:attachment/a:heading', namespaces={'a': doc.doc.namespace}):
            node.getparent().remove(node)

        # toc now includes `paragraph` (in main body of component fixture)
        toc = self.builder.table_of_contents_for_document(doc)
        self.assertEqual([{
            'type': 'paragraph',
            'component': 'main',
            'subcomponent': 'paragraph',
            'title': 'Paragraph',
            'basic_unit': False,
            'children': [],
        }, {
            'type': 'attachment',
            'component': 'schedule1',
            'subcomponent': None,
            'title': 'Schedule alias',
            'heading': 'Schedule alias',
            'id': 'att_1',
            'basic_unit': False,
            'children': [{
                'component': 'schedule1',
                'title': 'Section',
                'type': 'section',
                'id': 'sec_1',
                'subcomponent': 'section',
                'basic_unit': True,
                'children': [],
            }],
        }], [t.as_dict() for t in toc])
        self.assertEqual("att_1/sec_1", toc[1].children[0].qualified_id)

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

        toc = self.builder.table_of_contents_for_document(doc)
        tocs = [t.as_dict() for t in toc]
        toc_elements = flat_toc(tocs)
        self.assertEqual(len(toc_elements), 29)
        ids = [t.get('id') for t in toc_elements]
        self.assertEqual(
            ids,
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
             'dvs_nn_4', 'dvs_nn_4__para_25', 'dvs_nn_4__para_26',
             'dvs_nn_4__para_26__subpara_a',
             'dvs_nn_4__para_26__subpara_a__subpara_i',
             'dvs_nn_4__para_26__subpara_a__subpara_ii',
             'dvs_nn_4__para_26__subpara_a__subpara_iii',
             'dvs_nn_4__para_26__subpara_b']
        )

    def test_toc_item_below_section(self):
        doc = Document(
            work=self.work,
            document_xml=document_fixture(text="hi"),
            language=self.eng)

        elem = doc.doc.root.xpath("//*[@eId='sec_1']")[0]

        toc = self.builder.table_of_contents_entry_for_element(doc, elem)
        self.assertEqual(toc.as_dict(), {
            'component': 'main',
            'title': 'Section',
            'type': 'section',
            'id': 'sec_1',
            'subcomponent': 'section',
            'basic_unit': True,
            'children': [],
        })
        self.assertEqual(toc.id, toc.qualified_id)
