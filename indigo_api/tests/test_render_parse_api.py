from cobalt import datestring
from lxml import etree
import datetime
from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer

from indigo_api.tests.fixtures import *  # noqa


class RenderParseAPITest(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'work', 'published']

    def setUp(self):
        self.client.default_format = 'json'
        JSONRenderer.charset = 'utf-8'
        self.client.login(username='email@example.com', password='password')

    def test_render_with_null_publication(self):
        response = self.client.post('/api/documents/1/render/coverpage', {
            'document': {
                'content': document_fixture(text='hello'),
                'publication_name': None,
                'publication_number': None,
                'publication_date': None,
                'expression_date': '2001-01-01',
                'language': 'eng',
            },
        }, format='json')
        assert_equal(response.status_code, 200)

    def test_render_with_empty_publication(self):
        response = self.client.post('/api/documents/1/render/coverpage', {
            'document': {
                'content': document_fixture(text='hello'),
                'publication_name': '',
                'publication_number': '',
                'expression_date': '2001-01-01',
                'language': 'eng',
            },
        }, format='json')
        assert_equal(response.status_code, 200)

    def test_render_json_to_html(self):
        response = self.client.post('/api/documents/1/render/coverpage', {
            'document': {
                'content': document_fixture(text='hello'),
                'expression_date': '2001-01-01',
                'language': 'eng',
            },
        })
        assert_equal(response.status_code, 200)
        assert_in('<div class="coverpage">', response.data['output'])
        assert_in('Act 10 of 2014', response.data['output'])

    def test_render_json_to_html_round_trip(self):
        response = self.client.get('/api/documents/4.json')
        assert_equal(response.status_code, 200)

        data = response.data
        data['content'] = document_fixture(text='hello')

        response = self.client.post('/api/documents/4/render/coverpage', {
            'document': data,
        })
        assert_equal(response.status_code, 200)
        assert_in('<div class="coverpage">', response.data['output'])
        assert_in('Repealed Act', response.data['output'])

    def test_render_json_to_html_with_unicode(self):
        response = self.client.post('/api/documents/1/render/coverpage', {
            'document': {
                'content': document_fixture(text='hello κόσμε'),
                'expression_date': '2001-01-01',
                'language': 'eng',
            },
        })
        assert_equal(response.status_code, 200)
        assert_in('<div class="coverpage">', response.data['output'])
        assert_in('Act 10 of 2014', response.data['output'])

    def test_parse_text_fragment(self):
        response = self.client.post('/api/documents/1/parse', {
            'content': """
CHAPTER 2 - The Beginning

  SECTION 1. - First Verse

    κόσμε

    SUBSEC (1)

      In the beginning

    SUBSEC (2)

      There was nothing and an Act no 2 of 2010.
            """,
            'fragment': 'hier_element_block',
            'id_prefix': 'prefix',
            'language': 'eng',
        })
        self.assertEqual(response.status_code, 200)
        self.maxDiff = None
        # TODO: is it okay for  xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
        #  to be set on both chapter and wrapping akomaNtoso tag?
        self.assertEqual(
            response.data['output'],
            '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">'
            '<chapter xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" eId="prefix__chp_2"><num>2</num><heading>The Beginning</heading>'
            '<section eId="prefix__chp_2__sec_1"><num>1.</num><heading>First Verse</heading>'
            '<intro><p eId="prefix__chp_2__sec_1__intro__p_1">κόσμε</p></intro>'
            '<subsection eId="prefix__chp_2__sec_1__subsec_1"><num>(1)</num>'
            '<content><p eId="prefix__chp_2__sec_1__subsec_1__p_1">In the beginning</p></content></subsection>'
            '<subsection eId="prefix__chp_2__sec_1__subsec_2"><num>(2)</num>'
            '<content><p eId="prefix__chp_2__sec_1__subsec_2__p_1">There was nothing and an Act no 2 of 2010.</p>'
            '</content></subsection></section></chapter></akomaNtoso>'
        )

    def test_parse_text_with_components(self):
        response = self.client.post('/api/documents/1/parse', {
            'content': """
PREFACE

Under the powers vested in me by Sub-Article (5) of Article 26 of the Namibian Constitution, I, subsequent to having declared by Proclamation No. 7 of 18 March of 2020 that a State of Emergency exists in the whole of Namibia following a worldwide outbreak of the disease known as Coronavirus Disease 2019 (COVID-19) -

\(a) make the regulations set out in the Schedule; and

\(b) repeal the Stage 3: State of Emergency - Covid-19 Regulations published under Proclamation No. 32 of 6 July 2020.

Given under my Hand and the Seal of the Republic of Namibia at Windhoek, this 22nd day of July, Two Thousand and Twenty.

Hage G. Geingob

President

By order of the President

BODY

SEC 15. - Regulations to bind State

  These regulations bind the State.

SCHEDULE Annexure A
  SUBHEADING Critical services

  CROSSHEADING (Regulation 1)

  PART 1 - 

    PARA 1.

      Ambulance services

    PARA 2.

      Casualties services


  PART 2 - 

    SEC 1. - Agriculture and forestry

      Agricultural production and value chains (animal husbandry, agronomic and horticulture) supply related operations, including farming, veterinary and phyto-sanitary provider services, pest control services, feed and chemical and fertilizer providers. Millers and logistics services.

    SEC 2. - Fishing

      Harvesting of fish (including artisanal fishing other than for leisure), cultivation of fish and value chain activities relating to fish, as part of food production for Namibia and for export; maintenance of fishing vessels and maintenance of fishing processing plants.

SCHEDULE Annexure B
  SUBHEADING Essential goods

  CROSSHEADING (Regulation 1)

  PARA 1.

    Food:

    SUBPARA (a)

      any food product, including water and non-alcoholic beverages;

    SUBPARA (b)

      animal food; and

    SUBPARA (c)

      chemicals, packaging and ancillary products used in the production of any food product.

  PARA 4.

    Fuel, including coal and gas.

            """,
            'id_prefix': 'prefix',
            'language': 'eng',
        })
        self.assertEqual(response.status_code, 200)
        self.maxDiff = None

        actual = etree.tostring(
            etree.fromstring(response.data['output'].replace(datestring(datetime.date.today()), 'TODAY')),
            encoding='unicode', pretty_print=True)

        self.assertEqual(
            actual,
            '''<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act name="act"><meta>
      <identification source="">
        <FRBRWork>
          <FRBRthis value="/akn/za/act/2014/10/!main"/>
          <FRBRuri value="/akn/za/act/2014/10"/>
          <FRBRalias value="This is a title"/>
          <FRBRdate date="2014" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRcountry value="za"/><FRBRnumber value="10"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!main"/>
          <FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/>
          <FRBRdate date="2014-02-12" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!main"/>
          <FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/>
          <FRBRdate date="2015-02-04" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
        </FRBRManifestation>
      </identification>
      <publication date="2014-02-12" name="Name of publication" showAs="Name of publication" number="22"/>
    </meta>
    <preface><p eId="prefix__preface__p_1">Under the powers vested in me by Sub-Article (5) of Article 26 of the Namibian Constitution, I, subsequent to having declared by Proclamation No. 7 of 18 March of 2020 that a State of Emergency exists in the whole of Namibia following a worldwide outbreak of the disease known as Coronavirus Disease 2019 (COVID-19) -</p><p eId="prefix__preface__p_2">(a) make the regulations set out in the Schedule; and</p><p eId="prefix__preface__p_3">(b) repeal the Stage 3: State of Emergency - Covid-19 Regulations published under Proclamation No. 32 of 6 July 2020.</p><p eId="prefix__preface__p_4">Given under my Hand and the Seal of the Republic of Namibia at Windhoek, this 22nd day of July, Two Thousand and Twenty.</p><p eId="prefix__preface__p_5">Hage G. Geingob</p><p eId="prefix__preface__p_6">President</p><p eId="prefix__preface__p_7">By order of the President</p></preface><body><section eId="prefix__sec_15"><num>15.</num><heading>Regulations to bind State</heading><content><p eId="prefix__sec_15__p_1">These regulations bind the State.</p></content></section></body><attachments><attachment eId="prefix__att_1"><heading>Annexure A</heading><subheading>Critical services</subheading><doc name="schedule"><meta><identification source="#Indigo-Platform"><FRBRWork><FRBRthis value="/akn/za/act/2014/10/!schedule_1"/><FRBRuri value="/akn/za/act/2014/10"/><FRBRalias value="Annexure A" name="title"/><FRBRdate date="2014" name="Generation"/><FRBRauthor href=""/><FRBRcountry value="za"/><FRBRnumber value="10"/></FRBRWork><FRBRExpression><FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!schedule_1"/><FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/><FRBRdate date="TODAY" name="Generation"/><FRBRauthor href=""/><FRBRlanguage language="eng"/></FRBRExpression><FRBRManifestation><FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!schedule_1"/><FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/><FRBRdate date="TODAY" name="Generation"/><FRBRauthor href=""/></FRBRManifestation></identification></meta><mainBody><hcontainer name="hcontainer" eId="prefix__att_1__hcontainer_1"><crossHeading eId="prefix__att_1__hcontainer_1__crossHeading_1">(Regulation 1)</crossHeading></hcontainer><part eId="prefix__att_1__part_1"><num>1</num><paragraph eId="prefix__att_1__part_1__para_1"><num>1.</num><content><p eId="prefix__att_1__part_1__para_1__p_1">Ambulance services</p></content></paragraph><paragraph eId="prefix__att_1__part_1__para_2"><num>2.</num><content><p eId="prefix__att_1__part_1__para_2__p_1">Casualties services</p></content></paragraph></part><part eId="prefix__att_1__part_2"><num>2</num><section eId="prefix__att_1__part_2__sec_1"><num>1.</num><heading>Agriculture and forestry</heading><content><p eId="prefix__att_1__part_2__sec_1__p_1">Agricultural production and value chains (animal husbandry, agronomic and horticulture) supply related operations, including farming, veterinary and phyto-sanitary provider services, pest control services, feed and chemical and fertilizer providers. Millers and logistics services.</p></content></section><section eId="prefix__att_1__part_2__sec_2"><num>2.</num><heading>Fishing</heading><content><p eId="prefix__att_1__part_2__sec_2__p_1">Harvesting of fish (including artisanal fishing other than for leisure), cultivation of fish and value chain activities relating to fish, as part of food production for Namibia and for export; maintenance of fishing vessels and maintenance of fishing processing plants.</p></content></section></part></mainBody></doc></attachment><attachment eId="prefix__att_2"><heading>Annexure B</heading><subheading>Essential goods</subheading><doc name="schedule"><meta><identification source="#Indigo-Platform"><FRBRWork><FRBRthis value="/akn/za/act/2014/10/!schedule_2"/><FRBRuri value="/akn/za/act/2014/10"/><FRBRalias value="Annexure B" name="title"/><FRBRdate date="2014" name="Generation"/><FRBRauthor href=""/><FRBRcountry value="za"/><FRBRnumber value="10"/></FRBRWork><FRBRExpression><FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!schedule_2"/><FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/><FRBRdate date="TODAY" name="Generation"/><FRBRauthor href=""/><FRBRlanguage language="eng"/></FRBRExpression><FRBRManifestation><FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!schedule_2"/><FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/><FRBRdate date="TODAY" name="Generation"/><FRBRauthor href=""/></FRBRManifestation></identification></meta><mainBody><hcontainer name="hcontainer" eId="prefix__att_2__hcontainer_1"><crossHeading eId="prefix__att_2__hcontainer_1__crossHeading_1">(Regulation 1)</crossHeading></hcontainer><paragraph eId="prefix__att_2__para_1"><num>1.</num><intro><p eId="prefix__att_2__para_1__intro__p_1">Food:</p></intro><subparagraph eId="prefix__att_2__para_1__subpara_a"><num>(a)</num><content><p eId="prefix__att_2__para_1__subpara_a__p_1">any food product, including water and non-alcoholic beverages;</p></content></subparagraph><subparagraph eId="prefix__att_2__para_1__subpara_b"><num>(b)</num><content><p eId="prefix__att_2__para_1__subpara_b__p_1">animal food; and</p></content></subparagraph><subparagraph eId="prefix__att_2__para_1__subpara_c"><num>(c)</num><content><p eId="prefix__att_2__para_1__subpara_c__p_1">chemicals, packaging and ancillary products used in the production of any food product.</p></content></subparagraph></paragraph><paragraph eId="prefix__att_2__para_4"><num>4.</num><content><p eId="prefix__att_2__para_4__p_1">Fuel, including coal and gas.</p></content></paragraph></mainBody></doc></attachment></attachments></act>
</akomaNtoso>
'''
        )
