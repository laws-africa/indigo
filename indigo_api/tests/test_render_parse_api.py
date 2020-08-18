# -*- coding: utf-8 -*-

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
                Chapter 2
                The Beginning
                1. First Verse
                κόσμε
                (1) In the beginning
                (2) There was nothing and an Act no 2 of 2010.
            """,
            'fragment': 'chapter',
            'id_prefix': 'prefix',
            'language': 'eng',
        })
        self.assertEqual(response.status_code, 200)
        self.maxDiff = None
        self.assertEqual(
            response.data['output'],
            '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><chapter eId="prefix__chp_2"><num>2</num><heading>The Beginning</heading><section eId="sec_1"><num>1.</num><heading>First Verse</heading><hcontainer eId="sec_1__hcontainer_1" name="hcontainer"><content><p>κόσμε</p></content></hcontainer><subsection eId="sec_1__subsec_1"><num>(1)</num><content><p>In the beginning</p></content></subsection><subsection eId="sec_1__subsec_2"><num>(2)</num><content><p>There was nothing and an Act no 2 of 2010.</p></content></subsection></section></chapter></akomaNtoso>'
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

15. Regulations to bind State

These regulations bind the State.

SCHEDULE
HEADING Annexure A
SUBHEADING Critical services

CROSSHEADING (Regulation 1)

Part 1 - 

PARA 1. Ambulance services

PARA 2. Casualties services


Part 2 - 

1. Agriculture and forestry

Agricultural production and value chains (animal husbandry, agronomic and horticulture) supply related operations, including farming, veterinary and phyto-sanitary provider services, pest control services, feed and chemical and fertilizer providers. Millers and logistics services.

2. Fishing

Harvesting of fish (including artisanal fishing other than for leisure), cultivation of fish and value chain activities relating to fish, as part of food production for Namibia and for export; maintenance of fishing vessels and maintenance of fishing processing plants.

SCHEDULE
HEADING Annexure B
SUBHEADING Essential goods

CROSSHEADING (Regulation 1)

PARA 1. Food:

    (a) any food product, including water and non-alcoholic beverages;

    (b) animal food; and

    (c) chemicals, packaging and ancillary products used in the production of any food product.

PARA 4. Fuel, including coal and gas.

            """,
            'id_prefix': 'prefix',
            'language': 'eng',
        })
        self.assertEqual(response.status_code, 200)
        self.maxDiff = None
        self.assertEqual(
            response.data['output'],
            '''<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><act contains="originalVersion" name="act"><meta>
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
    <preface><p>Under the powers vested in me by Sub-Article (5) of Article 26 of the Namibian Constitution, I, subsequent to having declared by Proclamation No. 7 of 18 March of 2020 that a State of Emergency exists in the whole of Namibia following a worldwide outbreak of the disease known as Coronavirus Disease 2019 (COVID-19) -</p><p>(a) make the regulations set out in the Schedule; and</p><p>(b) repeal the Stage 3: State of Emergency - Covid-19 Regulations published under Proclamation No. 32 of 6 July 2020.</p><p>Given under my Hand and the Seal of the Republic of Namibia at Windhoek, this 22nd day of July, Two Thousand and Twenty.</p><p>Hage G. Geingob</p><p>President</p><p>By order of the President</p></preface><body><section eId="sec_15"><num>15.</num><heading>Regulations to bind State</heading><hcontainer eId="sec_15__hcontainer_1" name="hcontainer"><content><p>These regulations bind the State.</p></content></hcontainer></section></body><attachments><attachment eId="att_1"><heading>Annexure A</heading><subheading>Critical services</subheading><doc name="schedule"><meta><identification source="#slaw"><FRBRWork><FRBRthis value="/akn/za/act/2014/10/!annexurea"/><FRBRuri value="/akn/za/act/2014/10"/><FRBRalias value="Annexure A"/><FRBRdate date="2014" name="Generation"/><FRBRauthor href="#council"/><FRBRcountry value="za"/><FRBRnumber value="10"/></FRBRWork><FRBRExpression><FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!annexurea"/><FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/><FRBRdate date="1980-01-01" name="Generation"/><FRBRauthor href="#council"/><FRBRlanguage language="eng"/></FRBRExpression><FRBRManifestation><FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!annexurea"/><FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/><FRBRdate date="2020-08-18" name="Generation"/><FRBRauthor href="#slaw"/></FRBRManifestation></identification></meta><mainBody><hcontainer eId="hcontainer_1" name="crossheading"><heading>(Regulation 1)</heading></hcontainer><part eId="part_1"><num>1</num><hcontainer eId="part_1__hcontainer_1" name="hcontainer"><content><p>PARA 1. Ambulance services</p><p>PARA 2. Casualties services</p></content></hcontainer></part><part eId="part_2"><num>2</num><section eId="sec_1"><num>1.</num><heading>Agriculture and forestry</heading><hcontainer eId="sec_1__hcontainer_1" name="hcontainer"><content><p>Agricultural production and value chains (animal husbandry, agronomic and horticulture) supply related operations, including farming, veterinary and phyto-sanitary provider services, pest control services, feed and chemical and fertilizer providers. Millers and logistics services.</p></content></hcontainer></section><section eId="sec_2"><num>2.</num><heading>Fishing</heading><hcontainer eId="sec_2__hcontainer_1" name="hcontainer"><content><p>Harvesting of fish (including artisanal fishing other than for leisure), cultivation of fish and value chain activities relating to fish, as part of food production for Namibia and for export; maintenance of fishing vessels and maintenance of fishing processing plants.</p></content></hcontainer></section></part></mainBody></doc></attachment><attachment eId="att_2"><heading>Annexure B</heading><subheading>Essential goods</subheading><doc name="schedule"><meta><identification source="#slaw"><FRBRWork><FRBRthis value="/akn/za/act/2014/10/!annexureb"/><FRBRuri value="/akn/za/act/2014/10"/><FRBRalias value="Annexure B"/><FRBRdate date="2014" name="Generation"/><FRBRauthor href="#council"/><FRBRcountry value="za"/><FRBRnumber value="10"/></FRBRWork><FRBRExpression><FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!annexureb"/><FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/><FRBRdate date="1980-01-01" name="Generation"/><FRBRauthor href="#council"/><FRBRlanguage language="eng"/></FRBRExpression><FRBRManifestation><FRBRthis value="/akn/za/act/2014/10/eng@2014-02-12/!annexureb"/><FRBRuri value="/akn/za/act/2014/10/eng@2014-02-12"/><FRBRdate date="2020-08-18" name="Generation"/><FRBRauthor href="#slaw"/></FRBRManifestation></identification></meta><mainBody><hcontainer eId="hcontainer_1" name="crossheading"><heading>(Regulation 1)</heading></hcontainer><hcontainer eId="hcontainer_2" name="hcontainer"><content><blockList eId="hcontainer_2__list_1"><listIntroduction>PARA 1. Food:</listIntroduction><item eId="hcontainer_2__list_1__item_a"><num>(a)</num><p>any food product, including water and non-alcoholic beverages;</p></item><item eId="hcontainer_2__list_1__item_b"><num>(b)</num><p>animal food; and</p></item><item eId="hcontainer_2__list_1__item_c"><num>(c)</num><p>chemicals, packaging and ancillary products used in the production of any food product.</p></item></blockList><p>PARA 4. Fuel, including coal and gas.</p></content></hcontainer></mainBody></doc></attachment></attachments></act></akomaNtoso>'''
        )
