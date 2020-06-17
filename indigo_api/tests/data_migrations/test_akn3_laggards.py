# coding=utf-8
from collections import defaultdict
from datetime import date

from django.test import TestCase

from cobalt import Act

from indigo_api.data_migrations.akn3 import AKNeId, AKN3Laggards
from indigo_api.models import Document, Work, Annotation, Language, Country


class MigrationTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'work']
    maxDiff = None

    def setUp(self):
        self.za, self.cpt = Country.get_country_locality('za-cpt')
        self.eng = Language.for_code('eng')

    def test_full_migration(self):
        work = Work(country=self.za, locality=self.cpt, frbr_uri="/akn/za-cpt/act/by-law/2014/liquor-trading-days-and-hours")

        doc = Document(title="Liquor Trading Hours", frbr_uri="/akn/za-cpt/act/by-law/2014/liquor-trading-days-and-hours", work=work, language=self.eng, expression_date=date(2016, 8, 17), created_by_user_id=1, document_xml="""
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="singleVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/!main"/>
          <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours"/>
          <FRBRalias value="Liquor Trading Days and Hours"/>
          <FRBRdate date="2010-09-10" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
          <FRBRsubtype value="by-law"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26/!main"/>
          <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26"/>
          <FRBRdate date="2012-04-26" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26/!main"/>
          <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26"/>
          <FRBRdate date="2020-05-27" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="6788" name="Province of Western Cape: Provincial Gazette" showAs="Province of Western Cape: Provincial Gazette" date="2010-09-10"/>
      <lifecycle source="#Laws-Africa">
        <eventRef date="2012-04-26" type="amendment" source="#amendment-0-source" id="amendment-2012-04-26"/>
        <eventRef date="2014-01-17" type="repeal" source="#repeal-source" id="repeal-2014-01-17"/>
      </lifecycle>
      <references>
        <TLCOrganization href="https://edit.laws.africa" showAs="Laws.Africa" eId="Laws-Africa"/>
        <TLCOrganization href="https://github.com/longhotsummer/slaw" showAs="Slaw" eId="slaw"/>
        <TLCOrganization href="/ontology/organization/za/council" showAs="Council" eId="council"/>
        <TLCTerm showAs="agricultural area" href="/ontology/term/this.eng.agricultural_area" eId="term-agricultural_area"/>
        <passiveRef href="/akn/za-cpt/act/by-law/2012/liquor-trading-days-and-hours" showAs="Liquor Trading Days and Hours: Amendment" id="amendment-0-source"/>
        <passiveRef href="/akn/za-cpt/act/by-law/2014/control-undertakings-liquor" showAs="Control of Undertakings that Sell Liquor to the Public" id="repeal-source"/>
      </references>
    </meta>
    <preamble>
      <p>WHEREAS a municipality may, in terms of section 156 of the Constitution, make and administer by-laws for the effective administration of matters which it has the right to administer;</p>
      <p>WHEREAS it is the intention of the City to set trading days and hours for all licensed premises, businesses or outlet situated within the City of Cape Town that sell liquor to the public;</p>
      <p>AND NOW THEREFORE, BE IT ENACTED by the Council of the City of Cape Town, as follows:-</p>
    </preamble>
    <body>
      <section eId="sec_1">
        <num>1.</num>
        <heading>Definitions</heading>
        <subsection eId="sec_1__subsec_1">
          <num>(1)</num>
          <content>
            <p>In this By–Law, unless the context indicates otherwise-</p>
            <p refersTo="#term-agricultural_area">"<def refersTo="#term-agricultural_area">agricultural area</def>" means an area predominantly <term refersTo="#term-zoned" eId="sec_1__subsec_1__term_1">zoned</term> agriculture or any other equivalent zoning, with the purpose to promote and protect agricultural activity on a farm as an important economic, environmental and cultural resource, where limited provision is made for non-agricultural uses to provide owners with an opportunity to increase the economic potential of their properties, without causing a significant negative impact on the primary agricultural resource;</p>
          </content>
        </subsection>
      </section>
    </body>
    <attachments>
      <attachment eId="att_1">
        <heading>Schedule</heading>
        <subheading>Trading hours for selling of liquor on licensed premises</subheading>
        <doc name="schedule">
          <meta>
            <identification source="#slaw">
              <FRBRWork>
                <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/!schedule"/>
                <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours"/>
                <FRBRalias value="Schedule"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council"/>
                <FRBRcountry value="za"/>
                <FRBRsubtype value="by-law"/>
              </FRBRWork>
              <FRBRExpression>
                <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26/!schedule"/>
                <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council"/>
                <FRBRlanguage language="eng"/>
              </FRBRExpression>
              <FRBRManifestation>
                <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26/!schedule"/>
                <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26"/>
                <FRBRdate date="2020-05-27" name="Generation"/>
                <FRBRauthor href="#slaw"/>
              </FRBRManifestation>
            </identification>
          </meta>
          <mainBody>
            <hcontainer eId="hcontainer_1">
              <content>
                <table eId="hcontainer_1__table_1">
                  <tr>
                    <th>
                      <p>Location category &amp; licensed premises type</p>
                    </th>
                    <th>
                      <p>Maximum permitted trading hours</p>
                    </th>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
    </attachments>
  </act>
</akomaNtoso>
""")
        AKN3Laggards().migrate_act(doc.doc)
        output = doc.doc.to_xml(pretty_print=True, encoding='unicode')

        # check XML
        self.assertMultiLineEqual("""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="singleVersion" name="act">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/!main"/>
          <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours"/>
          <FRBRalias value="Liquor Trading Days and Hours" name="title"/>
          <FRBRdate date="2010-09-10" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za-cpt"/><FRBRnumber value="liquor-trading-days-and-hours"/>
          <FRBRsubtype value="by-law"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26/!main"/>
          <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26"/>
          <FRBRdate date="2012-04-26" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26/!main"/>
          <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26"/>
          <FRBRdate date="2020-05-27" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="6788" name="Province of Western Cape: Provincial Gazette" showAs="Province of Western Cape: Provincial Gazette" date="2010-09-10"/>
      <lifecycle source="#Laws-Africa">
        <eventRef date="2012-04-26" type="amendment" source="#amendment-0-source" eId="amendment-2012-04-26"/>
        <eventRef date="2014-01-17" type="repeal" source="#repeal-source" eId="repeal-2014-01-17"/>
      </lifecycle>
      <references source="#cobalt">
        <TLCOrganization href="https://edit.laws.africa" showAs="Laws.Africa" eId="Laws-Africa"/>
        <TLCOrganization href="https://github.com/longhotsummer/slaw" showAs="Slaw" eId="slaw"/>
        <TLCOrganization href="/ontology/organization/za/council" showAs="Council" eId="council"/>
        <TLCTerm showAs="agricultural area" href="/ontology/term/this.eng.agricultural_area" eId="term-agricultural_area"/>
        <passiveRef href="/akn/za-cpt/act/by-law/2012/liquor-trading-days-and-hours" showAs="Liquor Trading Days and Hours: Amendment" eId="amendment-0-source"/>
        <passiveRef href="/akn/za-cpt/act/by-law/2014/control-undertakings-liquor" showAs="Control of Undertakings that Sell Liquor to the Public" eId="repeal-source"/>
      </references>
    </meta>
    <preamble>
      <p>WHEREAS a municipality may, in terms of section 156 of the Constitution, make and administer by-laws for the effective administration of matters which it has the right to administer;</p>
      <p>WHEREAS it is the intention of the City to set trading days and hours for all licensed premises, businesses or outlet situated within the City of Cape Town that sell liquor to the public;</p>
      <p>AND NOW THEREFORE, BE IT ENACTED by the Council of the City of Cape Town, as follows:-</p>
    </preamble>
    <body>
      <section eId="sec_1">
        <num>1.</num>
        <heading>Definitions</heading>
        <subsection eId="sec_1__subsec_1">
          <num>(1)</num>
          <content>
            <p>In this By–Law, unless the context indicates otherwise-</p>
            <p refersTo="#term-agricultural_area">"<def refersTo="#term-agricultural_area">agricultural area</def>" means an area predominantly <term refersTo="#term-zoned" eId="sec_1__subsec_1__term_1">zoned</term> agriculture or any other equivalent zoning, with the purpose to promote and protect agricultural activity on a farm as an important economic, environmental and cultural resource, where limited provision is made for non-agricultural uses to provide owners with an opportunity to increase the economic potential of their properties, without causing a significant negative impact on the primary agricultural resource;</p>
          </content>
        </subsection>
      </section>
    </body>
    <attachments>
      <attachment eId="att_1">
        <heading>Schedule</heading>
        <subheading>Trading hours for selling of liquor on licensed premises</subheading>
        <doc name="schedule">
          <meta>
            <identification source="#slaw">
              <FRBRWork>
                <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/!schedule"/>
                <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours"/>
                <FRBRalias value="Schedule" name="title"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council"/>
                <FRBRcountry value="za-cpt"/><FRBRnumber value="liquor-trading-days-and-hours"/>
                <FRBRsubtype value="by-law"/>
              </FRBRWork>
              <FRBRExpression>
                <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26/!schedule"/>
                <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council"/>
                <FRBRlanguage language="eng"/>
              </FRBRExpression>
              <FRBRManifestation>
                <FRBRthis value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26/!schedule"/>
                <FRBRuri value="/akn/za-cpt/act/by-law/2010/liquor-trading-days-and-hours/eng@2012-04-26"/>
                <FRBRdate date="2020-05-27" name="Generation"/>
                <FRBRauthor href="#slaw"/>
              </FRBRManifestation>
            </identification>
          </meta>
          <mainBody>
            <hcontainer eId="hcontainer_1">
              <content>
                <table eId="hcontainer_1__table_1">
                  <tr>
                    <th>
                      <p>Location category &amp; licensed premises type</p>
                    </th>
                    <th>
                      <p>Maximum permitted trading hours</p>
                    </th>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
    </attachments>
  </act>
</akomaNtoso>
""", output)
