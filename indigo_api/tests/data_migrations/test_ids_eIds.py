# coding=utf-8
from datetime import date

from django.test import TestCase

from cobalt import Act

from indigo_api.data_migrations import AKNMigration, CrossheadingToHcontainer, UnnumberedParagraphsToHcontainer, ComponentSchedulesToAttachments, AKNeId, HrefMigration, AnnotationsMigration
from indigo_api.models import Document, Work, Annotation, Language


class MigrationTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'work']
    maxDiff = None

    def setUp(self):
        self.work = Work.objects.get(pk=1)
        self.eng = Language.for_code('eng')

    def test_safe_update(self):
        migration = AKNMigration()
        element = "foo"
        mappings = {"ABC": "XYZ"}
        with self.assertRaises(AssertionError):
            migration.safe_update(element, mappings, "ABC", "DEF")

    def test_full_migration(self):
        """ Include tests for:
            - CrossheadingToHcontainer
            - UnnumberedParagraphsToHcontainer
            - ComponentSchedulesToAttachments
            - AKNeId
            - HrefMigration
        """
        mappings = {}
        doc = Document(title="Air Quality Management", frbr_uri="/akn/za/act/2014/10", work=self.work, language=self.eng, expression_date=date(2016, 8, 17), created_by_user_id=1, document_xml="""
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/akn/za/act/2014/10/!main"/>
          <FRBRuri value="/akn/za/act/2014/10"/>
          <FRBRalias value="Air Quality Management" name="title"/>
          <FRBRdate date="" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!main"/>
          <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
          <FRBRdate date="2016-08-17" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!main"/>
          <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
          <FRBRdate date="2020-01-27" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="" name="" showAs="" date="2014-04-02"/>
    </meta>
    <body>
      <chapter id="chapter-I">
        <num>I</num>
        <heading>Definitions and fundamental principles</heading>
        <section id="section-1">
          <num>1.</num>
          <heading>Definitions</heading>
          <paragraph id="section-1.paragraph0">
            <content>
              <p>In this By-law, unless the context indicates otherwise -</p>
              <blockList id="section-1.paragraph0.list0" refersTo="#term-dark_smoke">
                <listIntroduction>"<def refersTo="#term-dark_smoke">dark smoke</def>" means-</listIntroduction>
                <item id="section-1.paragraph0.list0.a">
                  <num>(a)</num>
                  <p>in respect of Chapter V and Chapter VI of this By-law, <term refersTo="#term-smoke" id="trm21">smoke</term> which, when measured using a <term refersTo="#term-light_absorption_meter" id="trm22">light absorption meter</term>, <term refersTo="#term-obscuration" id="trm23">obscuration</term> measuring equipment or other similar equipment, has an <term refersTo="#term-obscuration" id="trm24">obscuration</term> of 20% or greater;</p>
                </item>
                <item id="section-1.paragraph0.list0.b">
                  <num>(b)</num>
                  <blockList id="section-1.paragraph0.list0.b.list0">
                    <listIntroduction>in respect of Chapter VIII of this By-law –</listIntroduction>
                    <item id="section-1.paragraph0.list0.b.list0.i">
                      <num>(i)</num>
                      <p><term refersTo="#term-smoke" id="trm25">smoke</term> emitted from the exhaust outlets of naturally aspirated compression ignition engines which has a density of 50 Hartridge <term refersTo="#term-smoke" id="trm26">smoke</term> units or more or a light absorption co-efficient of more than 1,61 mï1 ; or 18,57 percentage opacity; and</p>
                    </item>
                    <item id="section-1.paragraph0.list0.b.list0.ii">
                      <num>(ii)</num>
                      <p><term refersTo="#term-smoke" id="trm27">smoke</term> emitted from the exhaust outlets of turbo-charged compression ignition engines which has a density of 56 Hartridge <term refersTo="#term-smoke" id="trm28">smoke</term> units or more or a light absorption co-efficient of more than 1,91 mï1 ; or 21,57 percentage opacity.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
              <blockList id="section-1.paragraph0.list3" refersTo="#term-nuisance">
                <listIntroduction>"<def refersTo="#term-nuisance">nuisance</def>" means an unreasonable interference or likely interference caused by <term refersTo="#term-air_pollution" id="trm37">air pollution</term> which has an adverse impact on -</listIntroduction>
                <item id="section-1.paragraph0.list3.a">
                  <num>(a)</num>
                  <p>the health or well-being of any <term refersTo="#term-person" id="trm38">person</term> or <term refersTo="#term-living_organism" id="trm39">living organism</term>; or</p>
                </item>
                <item id="section-1.paragraph0.list3.b">
                  <num>(b)</num>
                  <p>the use and enjoyment by an owner or occupier of his or her property or the <term refersTo="#term-environment" id="trm40">environment</term>;</p>
                </item>
              </blockList>
            </content>
          </paragraph>
        </section>
        <section id="section-2">
          <num>2.</num>
          <heading>Application of this By-law</heading>
          <paragraph id="section-2.paragraph0">
            <content>
              <p>One paragraph.</p>
            </content>
          </paragraph>
          <paragraph id="section-2.paragraph1">
            <content>
              <p>Another paragraph.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <section id="section-2">
        <num>2.</num>
        <paragraph id="section-2.paragraph0">
          <content>
            <blockList id="section-2.paragraph0.list0">
              <listIntroduction>aoeuaoeu</listIntroduction>
              <item id="section-2.paragraph0.list0.a">
                <num>(a)</num>
                <blockList id="section-2.paragraph0.list0.a.list0">
                  <listIntroduction>aye</listIntroduction>
                  <item id="section-2.paragraph0.list0.a.list0.i">
                    <num>(i)</num>
                    <p>eye</p>
                  </item>
                </blockList>
              </item>
            </blockList>
          </content>
        </paragraph>
        <paragraph id="section-2.paragraph1">
          <content>
            <p>hi</p>
          </content>
        </paragraph>
      </section>
      <section id="section-4">
        <num>4.</num>
        <heading>Passive ref</heading>
        <subsection id="section-4.1">
          <num>(1)</num>
          <content>
            <p>XXX.</p>
          </content>
        </subsection>
        <subsection id="section-4.2">
          <num>(2)</num>
          <content>
            <p>YYY.</p>
          </content>
        </subsection>
      </section>
      <section id="section-6">
        <num>6.</num>
        <heading>Passive ref</heading>
        <subsection id="section-6.3">
          <num>(3)</num>
          <content>
            <blockList id="section-6.3.list0">
              <listIntroduction>In addition to imposing a fine or imprisonment, a court may order any person convicted of an offence under this By-law -</listIntroduction>
              <item id="section-6.3.list0.a">
                <num>(a)</num>
                <p>to remedy the harm caused; and</p>
              </item>
            </blockList>
          </content>
        </subsection>
      </section>
      <chapter id="chapter-XI">
        <num>XI</num>
        <heading>Offences and penalties</heading>
        <hcontainer id="chapter-XI.crossheading-0" name="crossheading">
          <heading>First in chapter</heading>
        </hcontainer>
        <section id="section-33">
          <num>33.</num>
          <heading>Offences and penalties</heading>
          <subsection id="section-33.1">
            <num>(1)</num>
            <content>
              <p>A person who contravenes sections <ref href="#section-4.1">4(1)</ref> and <ref href="#section-4.2">(2)</ref>, <ref href="#section-6.3.list0.a">6(3)(a)</ref>, <ref href="#section-2">2</ref>(1) and (2), etc. is guilty of an offence.</p>
            </content>
          </subsection>
          <subsection id="section-33.6">
            <num>(6)</num>
            <content>
              <blockList id="section-33.6.list0">
                <listIntroduction>In addition to imposing a fine or imprisonment, a court may order any person convicted of an offence under this By-law -</listIntroduction>
                <item id="section-33.6.list0.a">
                  <num>(a)</num>
                  <p>to remedy the harm caused; and</p>
                </item>
                <item id="section-33.6.list0.b">
                  <num>(b)</num>
                  <p>to pay damages for harm caused to another person or to property.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-34">
          <num>34.</num>
          <heading>Repeal and savings</heading>
          <subsection id="section-34.1">
            <num>(1)</num>
            <content>
              <p>The City of Cape Town: Air Quality Management By-law 2010 is hereby repealed.</p>
            </content>
          </subsection>
          <subsection id="section-34.2">
            <num>(2)</num>
            <content>
              <p>Anything done or deemed to have been done under any other by-law relating to air quality remains valid to the extent that it is consistent with this By-law.</p>
            </content>
          </subsection>
          <hcontainer id="section-34.crossheading-0" name="crossheading">
            <heading>Second in chapter</heading>
          </hcontainer>
        </section>
        <section id="section-35">
          <num>35.</num>
          <heading>Short title</heading>
          <hcontainer id="section-35.crossheading-0" name="crossheading">
            <heading>Inside a section</heading>
          </hcontainer>
          <paragraph id="section-35.paragraph0">
            <content>
              <p>This By-law is called the City of Cape Town: Air Quality Management By-law, 2016.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
    </body>
  </act>
  <components>
    <component id="component-schedule1">
      <doc name="schedule1">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/akn/za/act/2014/10/!schedule1"/>
              <FRBRuri value="/akn/za/act/2014/10"/>
              <FRBRalias value="Schedule 1"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!schedule1"/>
              <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!schedule1"/>
              <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
              <FRBRdate date="2019-12-05" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <hcontainer id="schedule1" name="schedule">
            <heading>Schedule 1</heading>
            <subheading>Standards and specifications for fuel-burning equipment:</subheading>
            <paragraph id="schedule1.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-4">
              <num>4.</num>
              <content>
                <p>The City reserves the right to call upon the owner or his or her agent of the fuel burning equipment to have the emissions from such fuel burning equipment evaluated at his or her own expense as may be required by the authorised official.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule1.crossheading-0" name="crossheading">
              <heading>Insulation of chimneys:</heading>
            </hcontainer>
            <paragraph id="schedule1.paragraph0">
              <content>
                <p>All fuel-burning equipment using Heavy Fuel Oil or other liquid fuels with a sulphur content equal to or greater than 2.5 % by weight must be fitted with a fully insulated chimney using either a 25mm air gap or mineral wool insulation to prevent the formation of acid smut. Such chimneys must be maintained in a good state of repair at all times.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule1.crossheading-1" name="crossheading">
              <heading>Wood-fired pizza ovens and other solid fuel combustion equipment:</heading>
            </hcontainer>
            <paragraph id="schedule1.paragraph1">
              <content>
                <p>Wood-fired pizza ovens and other solid fuel combustion equipment shall be fitted with induced draft fans at the discretion of the authorised official.</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule2">
      <doc name="schedule2">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/akn/za/act/2014/10/!schedule2"/>
              <FRBRuri value="/akn/za/act/2014/10"/>
              <FRBRalias value="Schedule 2"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!schedule2"/>
              <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!schedule2"/>
              <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
              <FRBRdate date="2019-12-05" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subheading>Good management practices to prevent or minimise the discharge of smoke from open burning of vegetation</subheading>
            <paragraph id="schedule2.paragraph-1">
              <num>1.</num>
              <content>
                <p>Consider alternatives to burning – e.g. mulching for recovery of nutrient value, drying for recovery as firewood.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-2">
              <num>2.</num>
              <content>
                <p>Vegetation that is to be burned (such as trimmings, pruning or felling’s cut from active growth) should as a general guide be allowed to dry to brown appearance prior to burning.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule2.crossheading-0" name="crossheading">
              <heading>Here's one</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph-3">
              <num>3.</num>
              <content>
                <p>Except for tree stumps or crop stubble, the place of combustion should be at least 50 metres from any road other than a highway, and 100 metres from any highway or dwelling on a neighbouring property.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule2.crossheading-1" name="crossheading">
              <heading>And another</heading>
            </hcontainer>
            <hcontainer id="schedule2.crossheading-2" name="crossheading">
              <heading>And more</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph-6">
              <num>6.</num>
              <content>
                <p>Two days' fine weather should be allowed prior to burning.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-7">
              <num>7.</num>
              <content>
                <p>Vegetation should be stacked loosely rather than compacted.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-8">
              <num>8.</num>
              <content>
                <p>A small fire, started with the driest material, with further material continually fed onto it once it is blazing, is preferable to a large stack ignited and left unattended.</p>
                <p><b>Note:</b> Persons conducting open burning of vegetation must ensure compliance with the requirements of the National Veld and Forest Fire Act, 1998, (<ref href="/za/act/1998/101">Act No. 101 of 1998</ref>) as amended.</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>
""")
        doc.save()
        annotation_anchors = {
            "section-2.paragraph0.list0.a.list0.i": "sec_2__hcontainer_1__list_1__item_a__list_1__item_i",
            "section-1.paragraph0": "sec_1__hcontainer_1",
            "chapter-XI.crossheading-0": "chp_XI__hcontainer_1",
            "schedule2.crossheading-1": "hcontainer_2",
            "schedule2.paragraph-1": "para_1",
        }
        for anchor_id in annotation_anchors.keys():
            annotation = Annotation(
                document=doc,
                created_by_user_id=1,
                anchor_id=anchor_id
            )
            annotation.save()

        cobalt_doc = Act(doc.document_xml)
        UnnumberedParagraphsToHcontainer().migrate_act(cobalt_doc, mappings)
        CrossheadingToHcontainer().migrate_act(cobalt_doc, mappings)
        ComponentSchedulesToAttachments().migrate_act(cobalt_doc, mappings)
        AKNeId().migrate_act(cobalt_doc, mappings)
        HrefMigration().migrate_act(cobalt_doc, mappings)
        AnnotationsMigration().migrate_act(doc, mappings)
        output = cobalt_doc.to_xml(pretty_print=True, encoding='unicode')
        today = date.today().strftime("%Y-%m-%d")

        # check XML
        self.assertMultiLineEqual(
            f"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/akn/za/act/2014/10/!main"/>
          <FRBRuri value="/akn/za/act/2014/10"/>
          <FRBRalias value="Air Quality Management" name="title"/>
          <FRBRdate date="2014-04-02" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!main"/>
          <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
          <FRBRdate date="2016-08-17" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!main"/>
          <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
          <FRBRdate date="{today}" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="" name="" showAs="" date="2014-04-02"/>
    </meta>
    <body>
      <chapter eId="chp_I">
        <num>I</num>
        <heading>Definitions and fundamental principles</heading>
        <section eId="sec_1">
          <num>1.</num>
          <heading>Definitions</heading>
          <hcontainer eId="sec_1__hcontainer_1">
            <content>
              <p>In this By-law, unless the context indicates otherwise -</p>
              <blockList refersTo="#term-dark_smoke" eId="sec_1__hcontainer_1__list_1">
                <listIntroduction>"<def refersTo="#term-dark_smoke">dark smoke</def>" means-</listIntroduction>
                <item eId="sec_1__hcontainer_1__list_1__item_a">
                  <num>(a)</num>
                  <p>in respect of Chapter V and Chapter VI of this By-law, <term refersTo="#term-smoke" eId="sec_1__hcontainer_1__list_1__item_a__term_1">smoke</term> which, when measured using a <term refersTo="#term-light_absorption_meter" eId="sec_1__hcontainer_1__list_1__item_a__term_2">light absorption meter</term>, <term refersTo="#term-obscuration" eId="sec_1__hcontainer_1__list_1__item_a__term_3">obscuration</term> measuring equipment or other similar equipment, has an <term refersTo="#term-obscuration" eId="sec_1__hcontainer_1__list_1__item_a__term_4">obscuration</term> of 20% or greater;</p>
                </item>
                <item eId="sec_1__hcontainer_1__list_1__item_b">
                  <num>(b)</num>
                  <blockList eId="sec_1__hcontainer_1__list_1__item_b__list_1">
                    <listIntroduction>in respect of Chapter VIII of this By-law –</listIntroduction>
                    <item eId="sec_1__hcontainer_1__list_1__item_b__list_1__item_i">
                      <num>(i)</num>
                      <p><term refersTo="#term-smoke" eId="sec_1__hcontainer_1__list_1__item_b__list_1__item_i__term_1">smoke</term> emitted from the exhaust outlets of naturally aspirated compression ignition engines which has a density of 50 Hartridge <term refersTo="#term-smoke" eId="sec_1__hcontainer_1__list_1__item_b__list_1__item_i__term_2">smoke</term> units or more or a light absorption co-efficient of more than 1,61 mï1 ; or 18,57 percentage opacity; and</p>
                    </item>
                    <item eId="sec_1__hcontainer_1__list_1__item_b__list_1__item_ii">
                      <num>(ii)</num>
                      <p><term refersTo="#term-smoke" eId="sec_1__hcontainer_1__list_1__item_b__list_1__item_ii__term_1">smoke</term> emitted from the exhaust outlets of turbo-charged compression ignition engines which has a density of 56 Hartridge <term refersTo="#term-smoke" eId="sec_1__hcontainer_1__list_1__item_b__list_1__item_ii__term_2">smoke</term> units or more or a light absorption co-efficient of more than 1,91 mï1 ; or 21,57 percentage opacity.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
              <blockList refersTo="#term-nuisance" eId="sec_1__hcontainer_1__list_4">
                <listIntroduction>"<def refersTo="#term-nuisance">nuisance</def>" means an unreasonable interference or likely interference caused by <term refersTo="#term-air_pollution" eId="sec_1__hcontainer_1__list_4__term_1">air pollution</term> which has an adverse impact on -</listIntroduction>
                <item eId="sec_1__hcontainer_1__list_4__item_a">
                  <num>(a)</num>
                  <p>the health or well-being of any <term refersTo="#term-person" eId="sec_1__hcontainer_1__list_4__item_a__term_1">person</term> or <term refersTo="#term-living_organism" eId="sec_1__hcontainer_1__list_4__item_a__term_2">living organism</term>; or</p>
                </item>
                <item eId="sec_1__hcontainer_1__list_4__item_b">
                  <num>(b)</num>
                  <p>the use and enjoyment by an owner or occupier of his or her property or the <term refersTo="#term-environment" eId="sec_1__hcontainer_1__list_4__item_b__term_1">environment</term>;</p>
                </item>
              </blockList>
            </content>
          </hcontainer>
        </section>
        <section eId="sec_2">
          <num>2.</num>
          <heading>Application of this By-law</heading>
          <hcontainer eId="sec_2__hcontainer_1">
            <content>
              <p>One paragraph.</p>
            </content>
          </hcontainer>
          <hcontainer eId="sec_2__hcontainer_2">
            <content>
              <p>Another paragraph.</p>
            </content>
          </hcontainer>
        </section>
      </chapter>
      <section eId="sec_2">
        <num>2.</num>
        <hcontainer eId="sec_2__hcontainer_1">
          <content>
            <blockList eId="sec_2__hcontainer_1__list_1">
              <listIntroduction>aoeuaoeu</listIntroduction>
              <item eId="sec_2__hcontainer_1__list_1__item_a">
                <num>(a)</num>
                <blockList eId="sec_2__hcontainer_1__list_1__item_a__list_1">
                  <listIntroduction>aye</listIntroduction>
                  <item eId="sec_2__hcontainer_1__list_1__item_a__list_1__item_i">
                    <num>(i)</num>
                    <p>eye</p>
                  </item>
                </blockList>
              </item>
            </blockList>
          </content>
        </hcontainer>
        <hcontainer eId="sec_2__hcontainer_2">
          <content>
            <p>hi</p>
          </content>
        </hcontainer>
      </section>
      <section eId="sec_4">
        <num>4.</num>
        <heading>Passive ref</heading>
        <subsection eId="sec_4__subsec_1">
          <num>(1)</num>
          <content>
            <p>XXX.</p>
          </content>
        </subsection>
        <subsection eId="sec_4__subsec_2">
          <num>(2)</num>
          <content>
            <p>YYY.</p>
          </content>
        </subsection>
      </section>
      <section eId="sec_6">
        <num>6.</num>
        <heading>Passive ref</heading>
        <subsection eId="sec_6__subsec_3">
          <num>(3)</num>
          <content>
            <blockList eId="sec_6__subsec_3__list_1">
              <listIntroduction>In addition to imposing a fine or imprisonment, a court may order any person convicted of an offence under this By-law -</listIntroduction>
              <item eId="sec_6__subsec_3__list_1__item_a">
                <num>(a)</num>
                <p>to remedy the harm caused; and</p>
              </item>
            </blockList>
          </content>
        </subsection>
      </section>
      <chapter eId="chp_XI">
        <num>XI</num>
        <heading>Offences and penalties</heading>
        <hcontainer name="crossheading" eId="chp_XI__hcontainer_1">
          <heading>First in chapter</heading>
        </hcontainer>
        <section eId="sec_33">
          <num>33.</num>
          <heading>Offences and penalties</heading>
          <subsection eId="sec_33__subsec_1">
            <num>(1)</num>
            <content>
              <p>A person who contravenes sections <ref href="#sec_4__subsec_1">4(1)</ref> and <ref href="#sec_4__subsec_2">(2)</ref>, <ref href="#sec_6__subsec_3__list_1__item_a">6(3)(a)</ref>, <ref href="#sec_2">2</ref>(1) and (2), etc. is guilty of an offence.</p>
            </content>
          </subsection>
          <subsection eId="sec_33__subsec_6">
            <num>(6)</num>
            <content>
              <blockList eId="sec_33__subsec_6__list_1">
                <listIntroduction>In addition to imposing a fine or imprisonment, a court may order any person convicted of an offence under this By-law -</listIntroduction>
                <item eId="sec_33__subsec_6__list_1__item_a">
                  <num>(a)</num>
                  <p>to remedy the harm caused; and</p>
                </item>
                <item eId="sec_33__subsec_6__list_1__item_b">
                  <num>(b)</num>
                  <p>to pay damages for harm caused to another person or to property.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section eId="sec_34">
          <num>34.</num>
          <heading>Repeal and savings</heading>
          <subsection eId="sec_34__subsec_1">
            <num>(1)</num>
            <content>
              <p>The City of Cape Town: Air Quality Management By-law 2010 is hereby repealed.</p>
            </content>
          </subsection>
          <subsection eId="sec_34__subsec_2">
            <num>(2)</num>
            <content>
              <p>Anything done or deemed to have been done under any other by-law relating to air quality remains valid to the extent that it is consistent with this By-law.</p>
            </content>
          </subsection>
          <hcontainer name="crossheading" eId="sec_34__hcontainer_1">
            <heading>Second in chapter</heading>
          </hcontainer>
        </section>
        <section eId="sec_35">
          <num>35.</num>
          <heading>Short title</heading>
          <hcontainer name="crossheading" eId="sec_35__hcontainer_1">
            <heading>Inside a section</heading>
          </hcontainer>
          <hcontainer eId="sec_35__hcontainer_2">
            <content>
              <p>This By-law is called the City of Cape Town: Air Quality Management By-law, 2016.</p>
            </content>
          </hcontainer>
        </section>
      </chapter>
    </body>
  <attachments>
    <attachment eId="att_1">
      <heading>Schedule 1</heading>
            <subheading>Standards and specifications for fuel-burning equipment:</subheading>
            <doc name="schedule">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/akn/za/act/2014/10/!!!!schedule1"/>
              <FRBRuri value="/akn/za/act/2014/10"/>
              <FRBRalias value="Schedule 1"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!!!!schedule1"/>
              <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!!!!schedule1"/>
              <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
              <FRBRdate date="2019-12-05" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <paragraph eId="para_1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph eId="para_2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph eId="para_3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
            <paragraph eId="para_4">
              <num>4.</num>
              <content>
                <p>The City reserves the right to call upon the owner or his or her agent of the fuel burning equipment to have the emissions from such fuel burning equipment evaluated at his or her own expense as may be required by the authorised official.</p>
              </content>
            </paragraph>
            <hcontainer name="crossheading" eId="hcontainer_1">
              <heading>Insulation of chimneys:</heading>
            </hcontainer>
            <hcontainer eId="hcontainer_2">
              <content>
                <p>All fuel-burning equipment using Heavy Fuel Oil or other liquid fuels with a sulphur content equal to or greater than 2.5 % by weight must be fitted with a fully insulated chimney using either a 25mm air gap or mineral wool insulation to prevent the formation of acid smut. Such chimneys must be maintained in a good state of repair at all times.</p>
              </content>
            </hcontainer>
            <hcontainer name="crossheading" eId="hcontainer_3">
              <heading>Wood-fired pizza ovens and other solid fuel combustion equipment:</heading>
            </hcontainer>
            <hcontainer eId="hcontainer_4">
              <content>
                <p>Wood-fired pizza ovens and other solid fuel combustion equipment shall be fitted with induced draft fans at the discretion of the authorised official.</p>
              </content>
            </hcontainer>
          </mainBody>
      </doc>
    </attachment>
    <attachment eId="att_2">
      <heading>Schedule 2</heading>
            <subheading>Good management practices to prevent or minimise the discharge of smoke from open burning of vegetation</subheading>
            <doc name="schedule">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/akn/za/act/2014/10/!!!!schedule2"/>
              <FRBRuri value="/akn/za/act/2014/10"/>
              <FRBRalias value="Schedule 2"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!!!!schedule2"/>
              <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/akn/za/act/2014/10/eng@2016-08-17/!!!!schedule2"/>
              <FRBRuri value="/akn/za/act/2014/10/eng@2016-08-17"/>
              <FRBRdate date="2019-12-05" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <paragraph eId="para_1">
              <num>1.</num>
              <content>
                <p>Consider alternatives to burning – e.g. mulching for recovery of nutrient value, drying for recovery as firewood.</p>
              </content>
            </paragraph>
            <paragraph eId="para_2">
              <num>2.</num>
              <content>
                <p>Vegetation that is to be burned (such as trimmings, pruning or felling’s cut from active growth) should as a general guide be allowed to dry to brown appearance prior to burning.</p>
              </content>
            </paragraph>
            <hcontainer name="crossheading" eId="hcontainer_1">
              <heading>Here's one</heading>
            </hcontainer>
            <paragraph eId="para_3">
              <num>3.</num>
              <content>
                <p>Except for tree stumps or crop stubble, the place of combustion should be at least 50 metres from any road other than a highway, and 100 metres from any highway or dwelling on a neighbouring property.</p>
              </content>
            </paragraph>
            <hcontainer name="crossheading" eId="hcontainer_2">
              <heading>And another</heading>
            </hcontainer>
            <hcontainer name="crossheading" eId="hcontainer_3">
              <heading>And more</heading>
            </hcontainer>
            <paragraph eId="para_6">
              <num>6.</num>
              <content>
                <p>Two days' fine weather should be allowed prior to burning.</p>
              </content>
            </paragraph>
            <paragraph eId="para_7">
              <num>7.</num>
              <content>
                <p>Vegetation should be stacked loosely rather than compacted.</p>
              </content>
            </paragraph>
            <paragraph eId="para_8">
              <num>8.</num>
              <content>
                <p>A small fire, started with the driest material, with further material continually fed onto it once it is blazing, is preferable to a large stack ignited and left unattended.</p>
                <p><b>Note:</b> Persons conducting open burning of vegetation must ensure compliance with the requirements of the National Veld and Forest Fire Act, 1998, (<ref href="/za/act/1998/101">Act No. 101 of 1998</ref>) as amended.</p>
              </content>
            </paragraph>
          </mainBody>
      </doc>
    </attachment>
  </attachments>
</act>
  </akomaNtoso>
""",
            output
        )

        # check mappings
        self.assertDictEqual(
            {
                "section-1.paragraph0": "section-1.hcontainer_1",
                "section-1.paragraph0.list0": "section-1.hcontainer_1.list0",
                "section-1.paragraph0.list0.a": "section-1.hcontainer_1.list0.a",
                "section-1.paragraph0.list0.b": "section-1.hcontainer_1.list0.b",
                "section-1.paragraph0.list0.b.list0": "section-1.hcontainer_1.list0.b.list0",
                "section-1.paragraph0.list0.b.list0.i": "section-1.hcontainer_1.list0.b.list0.i",
                "section-1.paragraph0.list0.b.list0.ii": "section-1.hcontainer_1.list0.b.list0.ii",
                "section-1.paragraph0.list3": "section-1.hcontainer_1.list3",
                "section-1.paragraph0.list3.a": "section-1.hcontainer_1.list3.a",
                "section-1.paragraph0.list3.b": "section-1.hcontainer_1.list3.b",
                "section-2.paragraph0": "section-2.hcontainer_1",
                "section-2.paragraph0.list0": "section-2.hcontainer_1.list0",
                "section-2.paragraph0.list0.a": "section-2.hcontainer_1.list0.a",
                "section-2.paragraph0.list0.a.list0": "section-2.hcontainer_1.list0.a.list0",
                "section-2.paragraph0.list0.a.list0.i": "section-2.hcontainer_1.list0.a.list0.i",
                "section-2.paragraph1": "section-2.hcontainer_2",
                "section-35.paragraph0": "section-35.hcontainer_2",
                "schedule1.paragraph0": "schedule1.hcontainer_2",
                "schedule1.paragraph1": "schedule1.hcontainer_4",
                "chapter-XI.crossheading-0": "chapter-XI.hcontainer_1",
                "section-34.crossheading-0": "section-34.hcontainer_1",
                "section-35.crossheading-0": "section-35.hcontainer_1",
                "schedule1.crossheading-0": "schedule1.hcontainer_1",
                "schedule1.crossheading-1": "schedule1.hcontainer_3",
                "schedule2.crossheading-0": "schedule2.hcontainer_1",
                "schedule2.crossheading-1": "schedule2.hcontainer_2",
                "schedule2.crossheading-2": "schedule2.hcontainer_3",
                "component-schedule1": "att_1",
                "schedule1.paragraph-1": "paragraph-1",
                "schedule1.paragraph-2": "paragraph-2",
                "schedule1.paragraph-3": "paragraph-3",
                "schedule1.paragraph-4": "paragraph-4",
                "schedule1.hcontainer_1": "hcontainer_1",
                "schedule1.hcontainer_2": "hcontainer_2",
                "schedule1.hcontainer_3": "hcontainer_3",
                "schedule1.hcontainer_4": "hcontainer_4",
                "component-schedule2": "att_2",
                "schedule2.paragraph-1": "paragraph-1",
                "schedule2.paragraph-2": "paragraph-2",
                "schedule2.hcontainer_1": "hcontainer_1",
                "schedule2.paragraph-3": "paragraph-3",
                "schedule2.hcontainer_2": "hcontainer_2",
                "schedule2.hcontainer_3": "hcontainer_3",
                "schedule2.paragraph-6": "paragraph-6",
                "schedule2.paragraph-7": "paragraph-7",
                "schedule2.paragraph-8": "paragraph-8",
                "chapter-I": "chp_I",
                "section-1": "sec_1",
                "section-1.hcontainer_1": "sec_1.hcontainer_1",
                "sec_1.hcontainer_1": "sec_1__hcontainer_1",

                "section-1.hcontainer_1.list0": "sec_1.hcontainer_1.list0",
                "sec_1.hcontainer_1.list0": "sec_1.hcontainer_1.list_1",
                "sec_1.hcontainer_1.list_1": "sec_1__hcontainer_1__list_1",

                "section-1.hcontainer_1.list0.a": "sec_1.hcontainer_1.list0.a",
                "sec_1.hcontainer_1.list0.a": "sec_1.hcontainer_1.list_1.a",
                "sec_1.hcontainer_1.list_1.a": "sec_1.hcontainer_1.list_1.item_a",
                "sec_1.hcontainer_1.list_1.item_a": "sec_1__hcontainer_1__list_1__item_a",
                'sec_1.hcontainer_1.list_1.item_a__term_1': 'sec_1__hcontainer_1__list_1__item_a__term_1',
                'sec_1.hcontainer_1.list_1.item_a__term_2': 'sec_1__hcontainer_1__list_1__item_a__term_2',
                'sec_1.hcontainer_1.list_1.item_a__term_3': 'sec_1__hcontainer_1__list_1__item_a__term_3',
                'sec_1.hcontainer_1.list_1.item_a__term_4': 'sec_1__hcontainer_1__list_1__item_a__term_4',

                "section-1.hcontainer_1.list0.b": "sec_1.hcontainer_1.list0.b",
                "sec_1.hcontainer_1.list0.b": "sec_1.hcontainer_1.list_1.b",
                "sec_1.hcontainer_1.list_1.b": "sec_1.hcontainer_1.list_1.item_b",
                "sec_1.hcontainer_1.list_1.item_b": "sec_1__hcontainer_1__list_1__item_b",
                'sec_1.hcontainer_1.list_1.item_b.list_1.item_i__term_1': 'sec_1__hcontainer_1__list_1__item_b__list_1__item_i__term_1',
                'sec_1.hcontainer_1.list_1.item_b.list_1.item_i__term_2': 'sec_1__hcontainer_1__list_1__item_b__list_1__item_i__term_2',

                "section-1.hcontainer_1.list0.b.list0": "sec_1.hcontainer_1.list0.b.list0",
                "sec_1.hcontainer_1.list0.b.list0": "sec_1.hcontainer_1.list_1.b.list0",
                "sec_1.hcontainer_1.list_1.b.list0": "sec_1.hcontainer_1.list_1.b.list_1",
                "sec_1.hcontainer_1.list_1.b.list_1": "sec_1.hcontainer_1.list_1.item_b.list_1",
                "sec_1.hcontainer_1.list_1.item_b.list_1": "sec_1__hcontainer_1__list_1__item_b__list_1",

                "section-1.hcontainer_1.list0.b.list0.i": "sec_1.hcontainer_1.list0.b.list0.i",
                "sec_1.hcontainer_1.list0.b.list0.i": "sec_1.hcontainer_1.list_1.b.list0.i",
                "sec_1.hcontainer_1.list_1.b.list0.i": "sec_1.hcontainer_1.list_1.b.list_1.i",
                "sec_1.hcontainer_1.list_1.b.list_1.i": "sec_1.hcontainer_1.list_1.item_b.list_1.i",
                "sec_1.hcontainer_1.list_1.item_b.list_1.i": "sec_1.hcontainer_1.list_1.item_b.list_1.item_i",
                "sec_1.hcontainer_1.list_1.item_b.list_1.item_i": "sec_1__hcontainer_1__list_1__item_b__list_1__item_i",

                "section-1.hcontainer_1.list0.b.list0.ii": "sec_1.hcontainer_1.list0.b.list0.ii",
                "sec_1.hcontainer_1.list0.b.list0.ii": "sec_1.hcontainer_1.list_1.b.list0.ii",
                "sec_1.hcontainer_1.list_1.b.list0.ii": "sec_1.hcontainer_1.list_1.b.list_1.ii",
                "sec_1.hcontainer_1.list_1.b.list_1.ii": "sec_1.hcontainer_1.list_1.item_b.list_1.ii",
                "sec_1.hcontainer_1.list_1.item_b.list_1.ii": "sec_1.hcontainer_1.list_1.item_b.list_1.item_ii",
                "sec_1.hcontainer_1.list_1.item_b.list_1.item_ii": "sec_1__hcontainer_1__list_1__item_b__list_1__item_ii",
                'sec_1.hcontainer_1.list_1.item_b.list_1.item_ii__term_1': 'sec_1__hcontainer_1__list_1__item_b__list_1__item_ii__term_1',
                'sec_1.hcontainer_1.list_1.item_b.list_1.item_ii__term_2': 'sec_1__hcontainer_1__list_1__item_b__list_1__item_ii__term_2',

                "section-1.hcontainer_1.list3": "sec_1.hcontainer_1.list3",
                "sec_1.hcontainer_1.list3": "sec_1.hcontainer_1.list_4",
                "sec_1.hcontainer_1.list_4": "sec_1__hcontainer_1__list_4",

                "section-1.hcontainer_1.list3.a": "sec_1.hcontainer_1.list3.a",
                "sec_1.hcontainer_1.list3.a": "sec_1.hcontainer_1.list_4.a",
                "sec_1.hcontainer_1.list_4.a": "sec_1.hcontainer_1.list_4.item_a",
                "sec_1.hcontainer_1.list_4.item_a": "sec_1__hcontainer_1__list_4__item_a",
                'sec_1.hcontainer_1.list_4.item_a__term_1': 'sec_1__hcontainer_1__list_4__item_a__term_1',
                'sec_1.hcontainer_1.list_4.item_a__term_2': 'sec_1__hcontainer_1__list_4__item_a__term_2',

                "section-1.hcontainer_1.list3.b": "sec_1.hcontainer_1.list3.b",
                "sec_1.hcontainer_1.list3.b": "sec_1.hcontainer_1.list_4.b",
                "sec_1.hcontainer_1.list_4.b": "sec_1.hcontainer_1.list_4.item_b",
                "sec_1.hcontainer_1.list_4.item_b": "sec_1__hcontainer_1__list_4__item_b",
                'sec_1.hcontainer_1.list_4.item_b__term_1': 'sec_1__hcontainer_1__list_4__item_b__term_1',
                'sec_1.hcontainer_1.list_4__term_1': 'sec_1__hcontainer_1__list_4__term_1',

                "section-2": "sec_2",

                "section-2.hcontainer_1": "sec_2.hcontainer_1",
                "sec_2.hcontainer_1": "sec_2__hcontainer_1",

                "section-2.hcontainer_1.list0": "sec_2.hcontainer_1.list0",
                "sec_2.hcontainer_1.list0": "sec_2.hcontainer_1.list_1",
                "sec_2.hcontainer_1.list_1": "sec_2__hcontainer_1__list_1",

                "section-2.hcontainer_1.list0.a": "sec_2.hcontainer_1.list0.a",
                "sec_2.hcontainer_1.list0.a": "sec_2.hcontainer_1.list_1.a",
                "sec_2.hcontainer_1.list_1.a": "sec_2.hcontainer_1.list_1.item_a",
                "sec_2.hcontainer_1.list_1.item_a": "sec_2__hcontainer_1__list_1__item_a",

                "section-2.hcontainer_1.list0.a.list0": "sec_2.hcontainer_1.list0.a.list0",
                "sec_2.hcontainer_1.list0.a.list0": "sec_2.hcontainer_1.list_1.a.list0",
                "sec_2.hcontainer_1.list_1.a.list0": "sec_2.hcontainer_1.list_1.a.list_1",
                "sec_2.hcontainer_1.list_1.a.list_1": "sec_2.hcontainer_1.list_1.item_a.list_1",
                "sec_2.hcontainer_1.list_1.item_a.list_1": "sec_2__hcontainer_1__list_1__item_a__list_1",

                "section-2.hcontainer_1.list0.a.list0.i": "sec_2.hcontainer_1.list0.a.list0.i",
                "sec_2.hcontainer_1.list0.a.list0.i": "sec_2.hcontainer_1.list_1.a.list0.i",
                "sec_2.hcontainer_1.list_1.a.list0.i": "sec_2.hcontainer_1.list_1.a.list_1.i",
                "sec_2.hcontainer_1.list_1.a.list_1.i": "sec_2.hcontainer_1.list_1.item_a.list_1.i",
                "sec_2.hcontainer_1.list_1.item_a.list_1.i": "sec_2.hcontainer_1.list_1.item_a.list_1.item_i",
                "sec_2.hcontainer_1.list_1.item_a.list_1.item_i": "sec_2__hcontainer_1__list_1__item_a__list_1__item_i",

                "section-2.hcontainer_2": "sec_2.hcontainer_2",
                "sec_2.hcontainer_2": "sec_2__hcontainer_2",

                "section-4": "sec_4",
                "section-4.1": "sec_4.1",
                "sec_4.1": "sec_4.subsec_1",
                "sec_4.subsec_1": "sec_4__subsec_1",

                "section-4.2": "sec_4.2",
                "sec_4.2": "sec_4.subsec_2",
                "sec_4.subsec_2": "sec_4__subsec_2",

                "section-6": "sec_6",
                "section-6.3": "sec_6.3",
                "sec_6.3": "sec_6.subsec_3",
                "sec_6.subsec_3": "sec_6__subsec_3",

                "section-6.3.list0": "sec_6.3.list0",
                "sec_6.3.list0": "sec_6.3.list_1",
                "sec_6.3.list_1": "sec_6.subsec_3.list_1",
                "sec_6.subsec_3.list_1": "sec_6__subsec_3__list_1",

                "section-6.3.list0.a": "sec_6.3.list0.a",
                "sec_6.3.list0.a": "sec_6.3.list_1.a",
                "sec_6.3.list_1.a": "sec_6.subsec_3.list_1.a",
                "sec_6.subsec_3.list_1.a": "sec_6.subsec_3.list_1.item_a",
                "sec_6.subsec_3.list_1.item_a": "sec_6__subsec_3__list_1__item_a",

                "chapter-XI": "chp_XI",
                "chapter-XI.hcontainer_1": "chp_XI.hcontainer_1",
                "chp_XI.hcontainer_1": "chp_XI__hcontainer_1",

                "section-33": "sec_33",
                "section-33.1": "sec_33.1",
                "sec_33.1": "sec_33.subsec_1",
                "sec_33.subsec_1": "sec_33__subsec_1",

                "section-33.6": "sec_33.6",
                "sec_33.6": "sec_33.subsec_6",
                "sec_33.subsec_6": "sec_33__subsec_6",

                "section-33.6.list0": "sec_33.6.list0",
                "sec_33.6.list0": "sec_33.6.list_1",
                "sec_33.6.list_1": "sec_33.subsec_6.list_1",
                "sec_33.subsec_6.list_1": "sec_33__subsec_6__list_1",

                "section-33.6.list0.a": "sec_33.6.list0.a",
                "sec_33.6.list0.a": "sec_33.6.list_1.a",
                "sec_33.6.list_1.a": "sec_33.subsec_6.list_1.a",
                "sec_33.subsec_6.list_1.a": "sec_33.subsec_6.list_1.item_a",
                "sec_33.subsec_6.list_1.item_a": "sec_33__subsec_6__list_1__item_a",

                "section-33.6.list0.b": "sec_33.6.list0.b",
                "sec_33.6.list0.b": "sec_33.6.list_1.b",
                "sec_33.6.list_1.b": "sec_33.subsec_6.list_1.b",
                "sec_33.subsec_6.list_1.b": "sec_33.subsec_6.list_1.item_b",
                "sec_33.subsec_6.list_1.item_b": "sec_33__subsec_6__list_1__item_b",

                "section-34": "sec_34",
                "section-34.1": "sec_34.1",
                "sec_34.1": "sec_34.subsec_1",
                "sec_34.subsec_1": "sec_34__subsec_1",

                "section-34.2": "sec_34.2",
                "sec_34.2": "sec_34.subsec_2",
                "sec_34.subsec_2": "sec_34__subsec_2",

                "section-34.hcontainer_1": "sec_34.hcontainer_1",
                "sec_34.hcontainer_1": "sec_34__hcontainer_1",

                "section-35": "sec_35",
                "section-35.hcontainer_1": "sec_35.hcontainer_1",
                "sec_35.hcontainer_1": "sec_35__hcontainer_1",
                "section-35.hcontainer_2": "sec_35.hcontainer_2",
                "sec_35.hcontainer_2": "sec_35__hcontainer_2",

                "paragraph-4": "para_4",
                "paragraph-1": "para_1",
                "paragraph-2": "para_2",
                "paragraph-3": "para_3",
                "paragraph-6": "para_6",
                "paragraph-7": "para_7",
                "paragraph-8": "para_8",

                'trm21': 'sec_1.hcontainer_1.list_1.item_a__term_1',
                'trm22': 'sec_1.hcontainer_1.list_1.item_a__term_2',
                'trm23': 'sec_1.hcontainer_1.list_1.item_a__term_3',
                'trm24': 'sec_1.hcontainer_1.list_1.item_a__term_4',
                'trm25': 'sec_1.hcontainer_1.list_1.item_b.list_1.item_i__term_1',
                'trm26': 'sec_1.hcontainer_1.list_1.item_b.list_1.item_i__term_2',
                'trm27': 'sec_1.hcontainer_1.list_1.item_b.list_1.item_ii__term_1',
                'trm28': 'sec_1.hcontainer_1.list_1.item_b.list_1.item_ii__term_2',
                'trm37': 'sec_1.hcontainer_1.list_4__term_1',
                'trm38': 'sec_1.hcontainer_1.list_4.item_a__term_1',
                'trm39': 'sec_1.hcontainer_1.list_4.item_a__term_2',
                'trm40': 'sec_1.hcontainer_1.list_4.item_b__term_1',
            },
            mappings
        )

        # check annotations
        new_annotations = doc.annotations.all()
        self.assertEqual(len(new_annotations), 5)
        for annotation in new_annotations:
            self.assertNotIn(annotation.anchor_id, mappings.keys())
            self.assertIn(annotation.anchor_id, mappings.values())

    def test_para_to_hcontainer(self):
        migration = UnnumberedParagraphsToHcontainer()

        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <chapter id="chapter-I">
        <num>I</num>
        <heading>Definitions and fundamental principles</heading>
        <section id="section-1">
          <num>1.</num>
          <heading>Definitions</heading>
          <paragraph id="section-1.paragraph0">
            <content>
              <p>In this By-law, unless the context indicates otherwise -</p>
              <p refersTo="#term-Council">"<def refersTo="#term-Council">Council</def>" means the Municipal Council of the <term refersTo="#term-City" id="trm20">City</term>;</p>
              <blockList id="section-1.paragraph0.list0" refersTo="#term-dark_smoke">
                <listIntroduction>"<def refersTo="#term-dark_smoke">dark smoke</def>" means-</listIntroduction>
                <item id="section-1.paragraph0.list0.a">
                  <num>(a)</num>
                  <p>in respect of Chapter V and Chapter VI of this By-law, <term refersTo="#term-smoke" id="trm21">smoke</term> which, when measured using a <term refersTo="#term-light_absorption_meter" id="trm22">light absorption meter</term>, <term refersTo="#term-obscuration" id="trm23">obscuration</term> measuring equipment or other similar equipment, has an <term refersTo="#term-obscuration" id="trm24">obscuration</term> of 20% or greater;</p>
                </item>
                <item id="section-1.paragraph0.list0.b">
                  <num>(b)</num>
                  <blockList id="section-1.paragraph0.list0.b.list0">
                    <listIntroduction>in respect of Chapter VIII of this By-law –</listIntroduction>
                    <item id="section-1.paragraph0.list0.b.list0.i">
                      <num>(i)</num>
                      <p><term refersTo="#term-smoke" id="trm25">smoke</term> emitted from the exhaust outlets of naturally aspirated compression ignition engines which has a density of 50 Hartridge <term refersTo="#term-smoke" id="trm26">smoke</term> units or more or a light absorption co-efficient of more than 1,61 mï1 ; or 18,57 percentage opacity; and</p>
                    </item>
                    <item id="section-1.paragraph0.list0.b.list0.ii">
                      <num>(ii)</num>
                      <p><term refersTo="#term-smoke" id="trm27">smoke</term> emitted from the exhaust outlets of turbo-charged compression ignition engines which has a density of 56 Hartridge <term refersTo="#term-smoke" id="trm28">smoke</term> units or more or a light absorption co-efficient of more than 1,91 mï1 ; or 21,57 percentage opacity.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
              <blockList id="section-1.paragraph0.list3" refersTo="#term-nuisance">
                <listIntroduction>"<def refersTo="#term-nuisance">nuisance</def>" means an unreasonable interference or likely interference caused by <term refersTo="#term-air_pollution" id="trm37">air pollution</term> which has an adverse impact on -</listIntroduction>
                <item id="section-1.paragraph0.list3.a">
                  <num>(a)</num>
                  <p>the health or well-being of any <term refersTo="#term-person" id="trm38">person</term> or <term refersTo="#term-living_organism" id="trm39">living organism</term>; or</p>
                </item>
                <item id="section-1.paragraph0.list3.b">
                  <num>(b)</num>
                  <p>the use and enjoyment by an owner or occupier of his or her property or the <term refersTo="#term-environment" id="trm40">environment</term>;</p>
                </item>
              </blockList>
            </content>
          </paragraph>
        </section>
        <section id="section-2">
          <num>2.</num>
          <heading>Application of this By-law</heading>
          <paragraph id="section-2.paragraph0">
            <content>
              <p>One paragraph.</p>
            </content>
          </paragraph>
          <paragraph id="section-2.paragraph1">
            <content>
              <p>Another paragraph.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <section id="section-2">
        <num>2.</num>
        <paragraph id="section-2.paragraph0">
          <content>
            <blockList id="section-2.paragraph0.list0">
              <listIntroduction>aoeuaoeu</listIntroduction>
              <item id="section-2.paragraph0.list0.a">
                <num>(a)</num>
                <blockList id="section-2.paragraph0.list0.a.list0">
                  <listIntroduction>aye</listIntroduction>
                  <item id="section-2.paragraph0.list0.a.list0.i">
                    <num>(i)</num>
                    <p>eye</p>
                  </item>
                </blockList>
              </item>
            </blockList>
          </content>
        </paragraph>
        <paragraph id="section-2.paragraph1">
          <content>
            <p>hi</p>
          </content>
        </paragraph>
      </section>
    </body>
  </act>
  <components>
    <component id="component-schedule1">
      <doc name="schedule1">
        <meta/>
        <mainBody>
          <hcontainer id="schedule1" name="schedule">
            <subheading>Subheading</subheading>
            <paragraph id="schedule1.paragraph0">
              <content>
                <p>schedule 1</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule2">
      <doc name="schedule2">
        <meta/>
        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
            <hcontainer id="schedule2.crossheading-0" name="crossheading">
              <heading>(Section 45(1))</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph0">
              <content>
                <p>hi</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule3">
      <doc name="schedule3">
        <meta/>
        <mainBody>
          <hcontainer id="schedule3" name="schedule">
            <heading>Schedule 3</heading>
            <subheading>Standards and specifications for fuel-burning equipment:</subheading>
            <paragraph id="schedule3.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-4">
              <num>4.</num>
              <content>
                <p>The City reserves the right to call upon the owner or his or her agent of the fuel burning equipment to have the emissions from such fuel burning equipment evaluated at his or her own expense as may be required by the authorised official.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule3.crossheading-0" name="crossheading">
              <heading>Insulation of chimneys:</heading>
            </hcontainer>
            <paragraph id="schedule3.paragraph0">
              <content>
                <p>All fuel-burning equipment using Heavy Fuel Oil or other liquid fuels with a sulphur content equal to or greater than 2.5 % by weight must be fitted with a fully insulated chimney using either a 25mm air gap or mineral wool insulation to prevent the formation of acid smut. Such chimneys must be maintained in a good state of repair at all times.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule3.crossheading-1" name="crossheading">
              <heading>Wood-fired pizza ovens and other solid fuel combustion equipment:</heading>
            </hcontainer>
            <paragraph id="schedule3.paragraph1">
              <content>
                <p>Wood-fired pizza ovens and other solid fuel combustion equipment shall be fitted with induced draft fans at the discretion of the authorised official.</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>
    """)
        migration.migrate_document(doc)
        doc.refresh_xml()
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <chapter id="chapter-I">
        <num>I</num>
        <heading>Definitions and fundamental principles</heading>
        <section id="section-1">
          <num>1.</num>
          <heading>Definitions</heading>
          <hcontainer id="section-1.hcontainer_1">
            <content>
              <p>In this By-law, unless the context indicates otherwise -</p>
              <p refersTo="#term-Council">"<def refersTo="#term-Council">Council</def>" means the Municipal Council of the <term refersTo="#term-City" id="trm20">City</term>;</p>
              <blockList id="section-1.hcontainer_1.list0" refersTo="#term-dark_smoke">
                <listIntroduction>"<def refersTo="#term-dark_smoke">dark smoke</def>" means-</listIntroduction>
                <item id="section-1.hcontainer_1.list0.a">
                  <num>(a)</num>
                  <p>in respect of Chapter V and Chapter VI of this By-law, <term refersTo="#term-smoke" id="trm21">smoke</term> which, when measured using a <term refersTo="#term-light_absorption_meter" id="trm22">light absorption meter</term>, <term refersTo="#term-obscuration" id="trm23">obscuration</term> measuring equipment or other similar equipment, has an <term refersTo="#term-obscuration" id="trm24">obscuration</term> of 20% or greater;</p>
                </item>
                <item id="section-1.hcontainer_1.list0.b">
                  <num>(b)</num>
                  <blockList id="section-1.hcontainer_1.list0.b.list0">
                    <listIntroduction>in respect of Chapter VIII of this By-law –</listIntroduction>
                    <item id="section-1.hcontainer_1.list0.b.list0.i">
                      <num>(i)</num>
                      <p><term refersTo="#term-smoke" id="trm25">smoke</term> emitted from the exhaust outlets of naturally aspirated compression ignition engines which has a density of 50 Hartridge <term refersTo="#term-smoke" id="trm26">smoke</term> units or more or a light absorption co-efficient of more than 1,61 mï1 ; or 18,57 percentage opacity; and</p>
                    </item>
                    <item id="section-1.hcontainer_1.list0.b.list0.ii">
                      <num>(ii)</num>
                      <p><term refersTo="#term-smoke" id="trm27">smoke</term> emitted from the exhaust outlets of turbo-charged compression ignition engines which has a density of 56 Hartridge <term refersTo="#term-smoke" id="trm28">smoke</term> units or more or a light absorption co-efficient of more than 1,91 mï1 ; or 21,57 percentage opacity.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
              <blockList id="section-1.hcontainer_1.list3" refersTo="#term-nuisance">
                <listIntroduction>"<def refersTo="#term-nuisance">nuisance</def>" means an unreasonable interference or likely interference caused by <term refersTo="#term-air_pollution" id="trm37">air pollution</term> which has an adverse impact on -</listIntroduction>
                <item id="section-1.hcontainer_1.list3.a">
                  <num>(a)</num>
                  <p>the health or well-being of any <term refersTo="#term-person" id="trm38">person</term> or <term refersTo="#term-living_organism" id="trm39">living organism</term>; or</p>
                </item>
                <item id="section-1.hcontainer_1.list3.b">
                  <num>(b)</num>
                  <p>the use and enjoyment by an owner or occupier of his or her property or the <term refersTo="#term-environment" id="trm40">environment</term>;</p>
                </item>
              </blockList>
            </content>
          </hcontainer>
        </section>
        <section id="section-2">
          <num>2.</num>
          <heading>Application of this By-law</heading>
          <hcontainer id="section-2.hcontainer_1">
            <content>
              <p>One paragraph.</p>
            </content>
          </hcontainer>
          <hcontainer id="section-2.hcontainer_2">
            <content>
              <p>Another paragraph.</p>
            </content>
          </hcontainer>
        </section>
      </chapter>
      <section id="section-2">
        <num>2.</num>
        <hcontainer id="section-2.hcontainer_1">
          <content>
            <blockList id="section-2.hcontainer_1.list0">
              <listIntroduction>aoeuaoeu</listIntroduction>
              <item id="section-2.hcontainer_1.list0.a">
                <num>(a)</num>
                <blockList id="section-2.hcontainer_1.list0.a.list0">
                  <listIntroduction>aye</listIntroduction>
                  <item id="section-2.hcontainer_1.list0.a.list0.i">
                    <num>(i)</num>
                    <p>eye</p>
                  </item>
                </blockList>
              </item>
            </blockList>
          </content>
        </hcontainer>
        <hcontainer id="section-2.hcontainer_2">
          <content>
            <p>hi</p>
          </content>
        </hcontainer>
      </section>
    </body>
  </act>
  <components>
    <component id="component-schedule1">
      <doc name="schedule1">
        <meta/>
        <mainBody>
          <hcontainer id="schedule1" name="schedule">
            <subheading>Subheading</subheading>
            <hcontainer id="schedule1.hcontainer_1">
              <content>
                <p>schedule 1</p>
              </content>
            </hcontainer>
            <paragraph id="schedule1.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule2">
      <doc name="schedule2">
        <meta/>
        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
            <hcontainer id="schedule2.crossheading-0" name="crossheading">
              <heading>(Section 45(1))</heading>
            </hcontainer>
            <hcontainer id="schedule2.hcontainer_2">
              <content>
                <p>hi</p>
              </content>
            </hcontainer>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule3">
      <doc name="schedule3">
        <meta/>
        <mainBody>
          <hcontainer id="schedule3" name="schedule">
            <heading>Schedule 3</heading>
            <subheading>Standards and specifications for fuel-burning equipment:</subheading>
            <paragraph id="schedule3.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-4">
              <num>4.</num>
              <content>
                <p>The City reserves the right to call upon the owner or his or her agent of the fuel burning equipment to have the emissions from such fuel burning equipment evaluated at his or her own expense as may be required by the authorised official.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule3.crossheading-0" name="crossheading">
              <heading>Insulation of chimneys:</heading>
            </hcontainer>
            <hcontainer id="schedule3.hcontainer_2">
              <content>
                <p>All fuel-burning equipment using Heavy Fuel Oil or other liquid fuels with a sulphur content equal to or greater than 2.5 % by weight must be fitted with a fully insulated chimney using either a 25mm air gap or mineral wool insulation to prevent the formation of acid smut. Such chimneys must be maintained in a good state of repair at all times.</p>
              </content>
            </hcontainer>
            <hcontainer id="schedule3.crossheading-1" name="crossheading">
              <heading>Wood-fired pizza ovens and other solid fuel combustion equipment:</heading>
            </hcontainer>
            <hcontainer id="schedule3.hcontainer_4">
              <content>
                <p>Wood-fired pizza ovens and other solid fuel combustion equipment shall be fitted with induced draft fans at the discretion of the authorised official.</p>
              </content>
            </hcontainer>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>""",
            doc.document_xml)

    def test_component_to_attachment(self):
        migration = ComponentSchedulesToAttachments()

        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body/>
  </act>
  <components>
    <component id="component-schedule1">
      <doc name="schedule1">
        <meta/>
        <mainBody>
          <hcontainer id="schedule1" name="schedule">
            <subheading>Subheading</subheading>
            <paragraph id="schedule1.paragraph0">
              <content>
                <p>schedule 1</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule2">
      <doc name="schedule2">
        <meta/>
        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
            <hcontainer id="schedule2.crossheading-0" name="crossheading">
              <heading>(Section 45(1))</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph0">
              <content>
                <p>hi</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>""")
        migration.migrate_document(doc)
        xml = doc.doc.to_xml(pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual("""<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body/>
  <attachments>
    <attachment id="att_1">
      <subheading>Subheading</subheading>
            <doc name="schedule">
        <meta/>
        <mainBody>
          <paragraph id="paragraph0">
              <content>
                <p>schedule 1</p>
              </content>
            </paragraph>
          </mainBody>
      </doc>
    </attachment>
    <attachment id="att_2">
      <heading>Schedule 2</heading>
            <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
            <doc name="schedule">
        <meta/>
        <mainBody>
          <hcontainer id="crossheading-0" name="crossheading">
              <heading>(Section 45(1))</heading>
            </hcontainer>
            <paragraph id="paragraph0">
              <content>
                <p>hi</p>
              </content>
            </paragraph>
          </mainBody>
      </doc>
    </attachment>
  </attachments>
</act>
  </akomaNtoso>
""", xml)

    def test_eid_basic(self):
        """ includes basic checks for
        meta elements,
        chapter, part, subpart, section, subsection, list, item
        """
        migration = AKNeId()

        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome"/>
          <FRBRalias value="Aerodromes"/>
          <FRBRdate date="2009-02-27" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27"/>
          <FRBRdate date="2009-02-27" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27"/>
          <FRBRdate date="2020-03-17" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="2042" name="Eastern Cape Provincial Gazette" showAs="Eastern Cape Provincial Gazette" date="2009-02-27"/>
      <lifecycle source="#OpenByLaws-org-za">
        <eventRef id="amendment-2011-08-05" date="2011-08-05" type="amendment" source="#amendment-0-source"/>
        <eventRef id="amendment-2013-11-01" date="2013-11-01" type="amendment" source="#amendment-1-source"/>
        <eventRef id="amendment-2016-11-04" date="2016-11-04" type="amendment" source="#amendment-2-source"/>
      </lifecycle>
      <references source="#this">
        <TLCOrganization id="slaw" href="https://github.com/longhotsummer/slaw" showAs="Slaw"/>
        <TLCOrganization id="council" href="/ontology/organization/za/council" showAs="Council"/>
        <TLCTerm id="term-aerodrome" showAs="aerodrome" href="/ontology/term/this.eng.aerodrome"/>
        <TLCTerm id="term-taxiway" showAs="taxiway" href="/ontology/term/this.eng.taxiway"/>
        <passiveRef id="amendment-0-source" href="/za-cpt/act/by-law/2011/sub-council-further-amendment" showAs="Cape Town Sub-council Further Amendment By-law, 2011"/>
        <passiveRef id="amendment-1-source" href="/za-cpt/act/by-law/2013/sub-council-amendment" showAs="Sub-council: Amendment"/>
        <passiveRef id="amendment-2-source" href="/za-cpt/act/by-law/2016/sub-council-amendment" showAs="Sub-Council: Amendment"/>
      </references>
    </meta>
    <preface>
      <longTitle>
        <p>To provide for air quality management and reasonable measures to prevent air pollution; to provide for the designation of the air quality officer; to provide for the establishment of local emissions norms and standards, and the promulgation of smoke control zones; to prohibit smoke emissions from dwellings and other premises; to provide for installation and operation of fuel burning equipment and obscuration measuring equipment, monitoring and sampling; to prohibit the emissions caused by dust, open burning and the burning of material; to prohibit dark smoke from compression ignition powered vehicles and provide for stopping, inspection and testing procedures; to prohibit emissions that cause a nuisance; to repeal the City of Cape Town: Air Quality Management By-law, 2010 and to provide for matters connected therewith;.</p>
      </longTitle>
    </preface>
    <preamble>
      <p>WHEREAS everyone has the constitutional right to an environment that is not harmful to their health or well-being;</p>
      <p>WHEREAS everyone has the constitutional right to have the environment protected, for the benefit of present and future generations, through reasonable legislative and other measures that–</p>
      <p>a) Prevent pollution and ecological degradation;</p>
      <p>b) Promote conservation; and</p>
      <p>c) Secure ecologically sustainable development and use of natural resources while promoting justifiable economic and social development;</p>
      <p>WHEREAS Part B of Schedule 4 of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> lists air pollution as a local government matter to the extent set out in section 155(6)(a) and (7);</p>
      <p>WHEREAS section 156(1)(a) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to administer local government matters listed in Part B of Schedule 4 and Part B of Schedule 5;</p>
      <p>WHEREAS section 156(2) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality may make and administer by-laws for the effective administration of the matters which it has the right to administer;</p>
      <p>WHEREAS section 156(5) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to exercise any power concerning a matter reasonably necessary for, or incidental to, the effective performance of its functions;</p>
      <p>AND WHEREAS the City of Cape Town seeks to ensure management of air quality and the control of air pollution within the area of jurisdiction of the City of Cape Town and to ensure that air pollution is avoided or, where it cannot be altogether avoided, is minimised and remedied.</p>
      <p>AND NOW THEREFORE, BE IT ENACTED by the Council of the City of Cape Town, as follows:-</p>
    </preamble>
    <body>
      <section id="section-1">
        <hcontainer id="section-1.hcontainer_1">
          <content>
            <p>text</p>
          </content>
        </hcontainer>
      </section>
      <section id="section-2">
        <num>2.</num>
        <heading>Powers of the caretaker</heading>
        <subsection id="section-2.1">
          <num>(1)</num>
          <content>
            <blockList id="section-2.1.list0">
              <listIntroduction>The Caretaker may-</listIntroduction>
              <item id="section-2.1.list0.a">
                <num>(a)</num>
                <p>prohibit any person who fails to pay an amount in respect of any facility on the aerodrome of which he makes use after such charges have become payable, to make use of any facility of the aerodrome:</p>
              </item>
              <item id="section-2.1.list0.b">
                <num>(b)</num>
                <p>should he for any reason deem it necessary at any time, for such period as he may determine, prohibit or limit the admission of people or vehicles, or both, to the aerodrome or to any particular area thereof;</p>
              </item>
              <item id="section-2.1.list0.c">
                <num>(c)</num>
                <p>order any person who, in his view, acts in such a way as to cause a nuisance or detrimentally affect the good management of the aerodrome to leave the aerodrome and if such person refuses to obey his order, take steps to have such person removed;</p>
              </item>
            </blockList>
          </content>
        </subsection>
        <subsection id="section-2.2.1">
          <num>2.1</num>
          <content>
            <p>Neither the Municipality nor the Caretaker must be liable for any loss or damage, whether directly or indirectly, owing to or arising from any act which the Caretaker performed or caused to be performed in terms of subsection (1)(d) or (e).</p>
          </content>
        </subsection>
      </section>
      <chapter id="chapter-6">
        <num>6</num>
        <part id="chapter-6.part-2">
          <num>2</num>
          <section id="section-3">
            <content>
              <p>The third section.</p>
            </content>
          </section>
          <section id="section-3A">
            <num>3A.</num>
            <subsection id="section-3A.1">
              <num>(1)</num>
              <content>
                <p>Section 3A, subsection (1).</p>
              </content>
            </subsection>
          </section>
        </part>
      </chapter>
      <part id="part-3">
        <num>3</num>
        <chapter id="part-3.chapter-1">
          <num>1</num>
          <section id="section-4">
            <content>
              <p>The fourth section.</p>
            </content>
          </section>
        </chapter>
      </part>
      <chapter id="chapter-XI">
        <num>XI</num>
        <heading>Offences and penalties</heading>
        <subpart id="chapter-XI.subpart-1">
          <num>1</num>
          <heading>First subpart</heading>
          <section id="section-33">
            <num>33.</num>
            <heading>Offences and penalties</heading>
            <subsection id="section-33.1">
              <num>(1)</num>
              <content>
                <p>A person who contravenes sections <ref href="#section-4">4</ref>(1) and (2), <ref href="#section-6">6</ref>(3), <ref href="#section-10">10</ref>(1) and (2), <ref href="#section-11">11</ref>(1), <ref href="#section-12">12</ref>(1), <ref href="#section-19">19</ref>(1), <ref href="#section-19">19</ref>(3), <ref href="#section-20">20</ref>(1), <ref href="#section-20">20</ref>(2), <ref href="#section-21">21</ref>(1), <ref href="#section-22">22</ref>(1), <ref href="#section-24">24</ref>(1), <ref href="#section-25">25</ref>(3), (4) , (5) and (6) , <ref href="#section-26">26</ref>(1), (2), (3) and (5), <ref href="#section-28">28</ref>(1), (2) and (3) is guilty of an offence.</p>
              </content>
            </subsection>
            <subsection id="section-33.6">
              <num>(6)</num>
              <content>
                <blockList id="section-33.6.list0">
                  <listIntroduction>In addition ... under this By-law -</listIntroduction>
                  <item id="section-33.6.list0.a">
                    <num>(a)</num>
                    <p>to remedy the harm caused; and</p>
                  </item>
                  <item id="section-33.6.list0.b">
                    <num>(b)</num>
                    <p>to pay damages for harm caused to another person or to property.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
          </section>
        </subpart>
        <subpart id="chapter-XI.subpart-2">
          <num>2</num>
          <heading>Second subpart</heading>
          <section id="section-34">
            <num>34.</num>
            <heading>Repeal and savings</heading>
            <subsection id="section-34.1">
              <num>(1)</num>
              <content>
                <p>The City of Cape Town: Air Quality Management By-law 2010 is hereby repealed.</p>
              </content>
            </subsection>
            <subsection id="section-34.2">
              <num>(2)</num>
              <content>
                <p>Anything done or deemed to have been done under any other by-law relating to air quality remains valid to the extent that it is consistent with this By-law.</p>
              </content>
            </subsection>
          </section>
          <section id="section-35">
            <num>35.</num>
            <heading>Short title</heading>
            <hcontainer id="section-35.hcontainer_1">
              <content>
                <p>This By-law is called the City of Cape Town: Air Quality Management By-law, 2016.</p>
              </content>
            </hcontainer>
          </section>
        </subpart>
      </chapter>
    </body>
  </act>
</akomaNtoso>""")
        migration.migrate_document(doc)
        output = doc.doc.to_xml(pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome"/>
          <FRBRalias value="Aerodromes"/>
          <FRBRdate date="2009-02-27" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27"/>
          <FRBRdate date="2009-02-27" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27"/>
          <FRBRdate date="2020-03-17" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="2042" name="Eastern Cape Provincial Gazette" showAs="Eastern Cape Provincial Gazette" date="2009-02-27"/>
      <lifecycle source="#OpenByLaws-org-za">
        <eventRef date="2011-08-05" type="amendment" source="#amendment-0-source" eId="amendment-2011-08-05"/>
        <eventRef date="2013-11-01" type="amendment" source="#amendment-1-source" eId="amendment-2013-11-01"/>
        <eventRef date="2016-11-04" type="amendment" source="#amendment-2-source" eId="amendment-2016-11-04"/>
      </lifecycle>
      <references source="#this">
        <TLCOrganization href="https://github.com/longhotsummer/slaw" showAs="Slaw" eId="slaw"/>
        <TLCOrganization href="/ontology/organization/za/council" showAs="Council" eId="council"/>
        <TLCTerm showAs="aerodrome" href="/ontology/term/this.eng.aerodrome" eId="term-aerodrome"/>
        <TLCTerm showAs="taxiway" href="/ontology/term/this.eng.taxiway" eId="term-taxiway"/>
        <passiveRef href="/za-cpt/act/by-law/2011/sub-council-further-amendment" showAs="Cape Town Sub-council Further Amendment By-law, 2011" eId="amendment-0-source"/>
        <passiveRef href="/za-cpt/act/by-law/2013/sub-council-amendment" showAs="Sub-council: Amendment" eId="amendment-1-source"/>
        <passiveRef href="/za-cpt/act/by-law/2016/sub-council-amendment" showAs="Sub-Council: Amendment" eId="amendment-2-source"/>
      </references>
    </meta>
    <preface>
      <longTitle>
        <p>To provide for air quality management and reasonable measures to prevent air pollution; to provide for the designation of the air quality officer; to provide for the establishment of local emissions norms and standards, and the promulgation of smoke control zones; to prohibit smoke emissions from dwellings and other premises; to provide for installation and operation of fuel burning equipment and obscuration measuring equipment, monitoring and sampling; to prohibit the emissions caused by dust, open burning and the burning of material; to prohibit dark smoke from compression ignition powered vehicles and provide for stopping, inspection and testing procedures; to prohibit emissions that cause a nuisance; to repeal the City of Cape Town: Air Quality Management By-law, 2010 and to provide for matters connected therewith;.</p>
      </longTitle>
    </preface>
    <preamble>
      <p>WHEREAS everyone has the constitutional right to an environment that is not harmful to their health or well-being;</p>
      <p>WHEREAS everyone has the constitutional right to have the environment protected, for the benefit of present and future generations, through reasonable legislative and other measures that–</p>
      <p>a) Prevent pollution and ecological degradation;</p>
      <p>b) Promote conservation; and</p>
      <p>c) Secure ecologically sustainable development and use of natural resources while promoting justifiable economic and social development;</p>
      <p>WHEREAS Part B of Schedule 4 of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> lists air pollution as a local government matter to the extent set out in section 155(6)(a) and (7);</p>
      <p>WHEREAS section 156(1)(a) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to administer local government matters listed in Part B of Schedule 4 and Part B of Schedule 5;</p>
      <p>WHEREAS section 156(2) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality may make and administer by-laws for the effective administration of the matters which it has the right to administer;</p>
      <p>WHEREAS section 156(5) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to exercise any power concerning a matter reasonably necessary for, or incidental to, the effective performance of its functions;</p>
      <p>AND WHEREAS the City of Cape Town seeks to ensure management of air quality and the control of air pollution within the area of jurisdiction of the City of Cape Town and to ensure that air pollution is avoided or, where it cannot be altogether avoided, is minimised and remedied.</p>
      <p>AND NOW THEREFORE, BE IT ENACTED by the Council of the City of Cape Town, as follows:-</p>
    </preamble>
    <body>
      <section eId="sec_1">
        <hcontainer eId="sec_1__hcontainer_1">
          <content>
            <p>text</p>
          </content>
        </hcontainer>
      </section>
      <section eId="sec_2">
        <num>2.</num>
        <heading>Powers of the caretaker</heading>
        <subsection eId="sec_2__subsec_1">
          <num>(1)</num>
          <content>
            <blockList eId="sec_2__subsec_1__list_1">
              <listIntroduction>The Caretaker may-</listIntroduction>
              <item eId="sec_2__subsec_1__list_1__item_a">
                <num>(a)</num>
                <p>prohibit any person who fails to pay an amount in respect of any facility on the aerodrome of which he makes use after such charges have become payable, to make use of any facility of the aerodrome:</p>
              </item>
              <item eId="sec_2__subsec_1__list_1__item_b">
                <num>(b)</num>
                <p>should he for any reason deem it necessary at any time, for such period as he may determine, prohibit or limit the admission of people or vehicles, or both, to the aerodrome or to any particular area thereof;</p>
              </item>
              <item eId="sec_2__subsec_1__list_1__item_c">
                <num>(c)</num>
                <p>order any person who, in his view, acts in such a way as to cause a nuisance or detrimentally affect the good management of the aerodrome to leave the aerodrome and if such person refuses to obey his order, take steps to have such person removed;</p>
              </item>
            </blockList>
          </content>
        </subsection>
        <subsection eId="sec_2__subsec_2-1">
          <num>2.1</num>
          <content>
            <p>Neither the Municipality nor the Caretaker must be liable for any loss or damage, whether directly or indirectly, owing to or arising from any act which the Caretaker performed or caused to be performed in terms of subsection (1)(d) or (e).</p>
          </content>
        </subsection>
      </section>
      <chapter eId="chp_6">
        <num>6</num>
        <part eId="chp_6__part_2">
          <num>2</num>
          <section eId="sec_3">
            <content>
              <p>The third section.</p>
            </content>
          </section>
          <section eId="sec_3A">
            <num>3A.</num>
            <subsection eId="sec_3A__subsec_1">
              <num>(1)</num>
              <content>
                <p>Section 3A, subsection (1).</p>
              </content>
            </subsection>
          </section>
        </part>
      </chapter>
      <part eId="part_3">
        <num>3</num>
        <chapter eId="part_3__chp_1">
          <num>1</num>
          <section eId="sec_4">
            <content>
              <p>The fourth section.</p>
            </content>
          </section>
        </chapter>
      </part>
      <chapter eId="chp_XI">
        <num>XI</num>
        <heading>Offences and penalties</heading>
        <subpart eId="chp_XI__subpart_1">
          <num>1</num>
          <heading>First subpart</heading>
          <section eId="sec_33">
            <num>33.</num>
            <heading>Offences and penalties</heading>
            <subsection eId="sec_33__subsec_1">
              <num>(1)</num>
              <content>
                <p>A person who contravenes sections <ref href="#section-4">4</ref>(1) and (2), <ref href="#section-6">6</ref>(3), <ref href="#section-10">10</ref>(1) and (2), <ref href="#section-11">11</ref>(1), <ref href="#section-12">12</ref>(1), <ref href="#section-19">19</ref>(1), <ref href="#section-19">19</ref>(3), <ref href="#section-20">20</ref>(1), <ref href="#section-20">20</ref>(2), <ref href="#section-21">21</ref>(1), <ref href="#section-22">22</ref>(1), <ref href="#section-24">24</ref>(1), <ref href="#section-25">25</ref>(3), (4) , (5) and (6) , <ref href="#section-26">26</ref>(1), (2), (3) and (5), <ref href="#section-28">28</ref>(1), (2) and (3) is guilty of an offence.</p>
              </content>
            </subsection>
            <subsection eId="sec_33__subsec_6">
              <num>(6)</num>
              <content>
                <blockList eId="sec_33__subsec_6__list_1">
                  <listIntroduction>In addition ... under this By-law -</listIntroduction>
                  <item eId="sec_33__subsec_6__list_1__item_a">
                    <num>(a)</num>
                    <p>to remedy the harm caused; and</p>
                  </item>
                  <item eId="sec_33__subsec_6__list_1__item_b">
                    <num>(b)</num>
                    <p>to pay damages for harm caused to another person or to property.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
          </section>
        </subpart>
        <subpart eId="chp_XI__subpart_2">
          <num>2</num>
          <heading>Second subpart</heading>
          <section eId="sec_34">
            <num>34.</num>
            <heading>Repeal and savings</heading>
            <subsection eId="sec_34__subsec_1">
              <num>(1)</num>
              <content>
                <p>The City of Cape Town: Air Quality Management By-law 2010 is hereby repealed.</p>
              </content>
            </subsection>
            <subsection eId="sec_34__subsec_2">
              <num>(2)</num>
              <content>
                <p>Anything done or deemed to have been done under any other by-law relating to air quality remains valid to the extent that it is consistent with this By-law.</p>
              </content>
            </subsection>
          </section>
          <section eId="sec_35">
            <num>35.</num>
            <heading>Short title</heading>
            <hcontainer eId="sec_35__hcontainer_1">
              <content>
                <p>This By-law is called the City of Cape Town: Air Quality Management By-law, 2016.</p>
              </content>
            </hcontainer>
          </section>
        </subpart>
      </chapter>
    </body>
  </act>
</akomaNtoso>
""",
            output
        )

    def test_eid_item(self):
        """ includes checks for list, item, and nested lists
        """
        migration = AKNeId()
        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <section id="section-100">
        <subsection id="section-100.3A.2">
          <blockList id="section-100.3A.2.list6">
            <item id="section-100.3A.2.list6.i">
              <p>item text</p>
            </item>
            <item id="section-100.3A.2.list6.ii.c">
              <p>item text</p>
            </item>
            <item id="section-100.3A.2.list6.iii">
              <blockList id="section-100.3A.2.list6.iii.list0">
                <item id="section-100.3A.2.list6.iii.list0.a">
                  <p>item text</p>
                </item>
                <item id="section-100.3A.2.list6.iii.list0.b.1.i">
                  <p>item text</p>
                </item>
              </blockList>
            </item>
          </blockList>
        </subsection>
      </section>
    </body>
  </act>
</akomaNtoso>""")
        migration.migrate_document(doc)
        output = doc.doc.to_xml(pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <section eId="sec_100">
        <subsection eId="sec_100__subsec_3A-2">
          <blockList eId="sec_100__subsec_3A-2__list_7">
            <item eId="sec_100__subsec_3A-2__list_7__item_i">
              <p>item text</p>
            </item>
            <item eId="sec_100__subsec_3A-2__list_7__item_ii-c">
              <p>item text</p>
            </item>
            <item eId="sec_100__subsec_3A-2__list_7__item_iii">
              <blockList eId="sec_100__subsec_3A-2__list_7__item_iii__list_1">
                <item eId="sec_100__subsec_3A-2__list_7__item_iii__list_1__item_a">
                  <p>item text</p>
                </item>
                <item eId="sec_100__subsec_3A-2__list_7__item_iii__list_1__item_b-1-i">
                  <p>item text</p>
                </item>
              </blockList>
            </item>
          </blockList>
        </subsection>
      </section>
    </body>
  </act>
</akomaNtoso>
""",
            output
        )

    def test_eid_schedule(self):
        """ includes checks for
        Schedules, annexures, chapter, part, crossheading, anonymous and numbered paragraphs, article, section
        """
        migration = AKNeId()
        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="singleVersion">
    <meta/>
    <body/>
    <attachments>
      <attachment id="att_1">
        <heading>Annexure</heading>
        <subheading>Things to do during lockdown</subheading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer id="hcontainer_1" name="crossheading">
              <heading>Form A</heading>
            </hcontainer>
            <hcontainer id="hcontainer_2">
              <content>
                <p>I ................. hereby ...............</p>
                <p>Signed</p>
              </content>
            </hcontainer>
            <hcontainer id="hcontainer_3" name="crossheading">
              <heading>Form B</heading>
            </hcontainer>
            <hcontainer id="hcontainer_4">
              <content>
                <p>One may:</p>
              </content>
            </hcontainer>
            <paragraph id="paragraph-1">
              <num>1.</num>
              <content>
                <p>Sing</p>
              </content>
            </paragraph>
            <paragraph id="paragraph-2">
              <num>2.</num>
              <content>
                <p>Dance</p>
              </content>
            </paragraph>
            <paragraph id="paragraph-3">
              <num>3.</num>
              <content>
                <p>Sway</p>
              </content>
            </paragraph>
            <hcontainer id="hcontainer_5" name="crossheading">
              <heading>Form C</heading>
            </hcontainer>
            <section id="section-1">
              <num>1.</num>
              <heading>Paragraph heading</heading>
              <subsection id="section-1.1">
                <num>(1)</num>
                <content>
                  <p>sdfkhsdkjfhldfh.</p>
                </content>
              </subsection>
              <subsection id="section-1.2">
                <num>(2)</num>
                <content>
                  <p>sldfhsdkfnldksn.</p>
                </content>
              </subsection>
            </section>
            <section id="section-2">
              <num>2.</num>
              <heading>Another heading</heading>
              <subsection id="section-2.1">
                <num>(1)</num>
                <content>
                  <p>dskfahsdkfdnsv.dn.</p>
                </content>
              </subsection>
              <subsection id="section-2.2">
                <num>(2)</num>
                <content>
                  <p>sdfkdskvdnvmbdvmsnd.</p>
                </content>
              </subsection>
            </section>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_2">
        <heading>Schedule 1</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer id="hcontainer_1">
              <content>
                <table id="hcontainer_1.table0">
                  <tr>
                    <th>
                      <p>Column 1</p>
                    </th>
                    <th>
                      <p>Column 2</p>
                    </th>
                    <th>
                      <p>Column 3</p>
                    </th>
                  </tr>
                  <tr>
                    <th>
                      <p>Sub-Council Designation</p>
                    </th>
                    <th>
                      <p>Sub-Council Name</p>
                    </th>
                    <th>
                      <p>Ward Numbers</p>
                    </th>
                  </tr>
                  <tr>
                    <td>
                      <p>1</p>
                    </td>
                    <td>
                      <p>Subcouncil 1 Blaauwberg</p>
                    </td>
                    <td>
                      <p>4, 23, 29, 32, 104, 107</p>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <p>2</p>
                    </td>
                    <td>
                      <p>Subcouncil 2 Bergdal</p>
                    </td>
                    <td>
                      <p>6, 7, 8, 111</p>
                    </td>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_3">
        <heading>Schedule 2</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer id="hcontainer_1">
              <content>
                <table id="hcontainer_1.table0">
                  <tr>
                    <th>
                      <p>COLUMN 1</p>
                    </th>
                    <th>
                      <p>COLUMN 2</p>
                    </th>
                  </tr>
                  <tr>
                    <th>
                      <p>SUB-COUNCIL DESIGNATION</p>
                    </th>
                    <th>
                      <p>WARD NUMBERS</p>
                    </th>
                  </tr>
                  <tr>
                    <td>
                      <p>1</p>
                    </td>
                    <td>
                      <p>23, 29, 32 and 104</p>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <p>2</p>
                    </td>
                    <td>
                      <p>6, 7, 8, 101, 102 and 111</p>
                    </td>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_4">
        <heading>Third Schedule</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <chapter id="chapter-1">
              <num>1</num>
              <heading>The first Chapter</heading>
              <part id="chapter-1.part-1">
                <num>1</num>
                <heading>The first Part</heading>
                <paragraph id="chapter-1.part-1.paragraph-1">
                  <num>1.</num>
                  <content>
                    <p>The first para</p>
                  </content>
                </paragraph>
                <paragraph id="chapter-1.part-1.paragraph-2">
                  <num>2.</num>
                  <content>
                    <p>The second para</p>
                  </content>
                </paragraph>
                <paragraph id="chapter-1.part-1.paragraph-345456">
                  <num>345456.</num>
                  <content>
                    <p>The last para</p>
                  </content>
                </paragraph>
              </part>
              <part id="chapter-1.part-2">
                <num>2</num>
                <heading>The second Part</heading>
                <paragraph id="chapter-1.part-2.paragraph-1">
                  <num>1.</num>
                  <content>
                    <p>Starting all over again</p>
                  </content>
                </paragraph>
                <paragraph id="chapter-1.part-2.paragraph-2">
                  <num>2.</num>
                  <content>
                    <p>Yup</p>
                  </content>
                </paragraph>
                <paragraph id="chapter-1.part-2.paragraph-3">
                  <num>3.</num>
                  <content>
                    <p>sdflkdsjg;ndfg</p>
                  </content>
                </paragraph>
              </part>
            </chapter>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_5">
        <heading>Fourth Schedule</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <part id="part-36">
              <num>36</num>
              <heading>Let's get nested</heading>
              <chapter id="part-36.chapter-A">
                <num>A</num>
                <heading>Nested Chapter</heading>
                <section id="section-1">
                  <num>1.</num>
                  <heading>fjlhsdkfh</heading>
                  <hcontainer id="section-1.hcontainer_1">
                    <content>
                      <p>dsjfhsdkjfhkshdf</p>
                    </content>
                  </hcontainer>
                </section>
                <section id="section-300">
                  <num>300.</num>
                  <heading>skdfhdkshfasd</heading>
                  <hcontainer id="section-300.hcontainer_1">
                    <content>
                      <p>asfjhadjslgfjsdghfjhg</p>
                    </content>
                  </hcontainer>
                </section>
              </chapter>
              <chapter id="part-36.chapter-B">
                <num>B</num>
                <heading>Still inside</heading>
                <section id="section-301">
                  <num>301.</num>
                  <heading>skhfdsjghfd</heading>
                  <hcontainer id="section-301.hcontainer_1">
                    <content>
                      <p>sdfjsdlgjlkdfjg</p>
                    </content>
                  </hcontainer>
                </section>
                <section id="section-302">
                  <num>302.</num>
                  <heading>dkfhdsjhgdbfhjg</heading>
                  <hcontainer id="section-302.hcontainer_1">
                    <content>
                      <blockList id="section-302.hcontainer_1.list0">
                        <listIntroduction>And let's nest a list:</listIntroduction>
                        <item id="section-302.hcontainer_1.list0.1">
                          <num>(1)</num>
                          <p>These ones are weird:</p>
                          <blockList id="section-302.hcontainer_1.list0.1.list0">
                            <listIntroduction><remark status="editorial">[editorial remark]</remark></listIntroduction>
                            <item id="section-302.hcontainer_1.list0.1.list0.a">
                              <num>(a)</num>
                              <p>sfhsdkjfhksdh;</p>
                            </item>
                            <item id="section-302.hcontainer_1.list0.1.list0.b">
                              <num>(b)</num>
                              <p>sdfhsdnfbmnsdbf;</p>
                              <p><remark status="editorial">[editorial remark]</remark></p>
                            </item>
                            <item id="section-302.hcontainer_1.list0.1.list0.c">
                              <num>(c)</num>
                              <p>jshaasbmnbxc.</p>
                            </item>
                          </blockList>
                        </item>
                        <item id="section-302.hcontainer_1.list0.2">
                          <num>(2)</num>
                          <p>A nother not-quite subsection.</p>
                        </item>
                      </blockList>
                    </content>
                  </hcontainer>
                </section>
              </chapter>
            </part>
            <part id="part-37">
              <num>37</num>
              <heading>Back out to the top level</heading>
              <section id="section-303">
                <num>303.</num>
                <heading>sfsjdbfbsdjnfb</heading>
                <subsection id="section-303.1">
                  <num>(1)</num>
                  <content>
                    <p>Normal subsection:</p>
                    <blockList id="section-303.1.list0">
                      <listIntroduction>Normal list:</listIntroduction>
                      <item id="section-303.1.list0.a">
                        <num>(a)</num>
                        <p>normal item;</p>
                      </item>
                      <item id="section-303.1.list0.a">
                        <num>(a)</num>
                        <p>normal item (duplicate number);</p>
                      </item>
                      <item id="section-303.1.list0.a">
                        <num>(a)</num>
                        <blockList id="section-303.1.list0.a.list0">
                          <listIntroduction>normal item (also duplicate):</listIntroduction>
                          <item id="section-303.1.list0.a.list0.i">
                            <num>(i)</num>
                            <blockList id="section-303.1.list0.a.list0.i.list0">
                              <listIntroduction>sublist item, plus:</listIntroduction>
                              <item id="section-303.1.list0.a.list0.i.list0.A">
                                <num>(A)</num>
                                <p>nested further!</p>
                              </item>
                              <item id="section-303.1.list0.a.list0.i.list0.B">
                                <num>(B)</num>
                                <p>nested further!</p>
                              </item>
                              <item id="section-303.1.list0.a.list0.i.list0.B">
                                <num>(B)</num>
                                <p>nested further!</p>
                              </item>
                            </blockList>
                          </item>
                          <item id="section-303.1.list0.a.list0.ii">
                            <num>(ii)</num>
                            <p>moar; and</p>
                          </item>
                        </blockList>
                      </item>
                      <item id="section-303.1.list0.b">
                        <num>(b)</num>
                        <p>final item.</p>
                      </item>
                    </blockList>
                  </content>
                </subsection>
                <hcontainer id="section-303.hcontainer_1" name="crossheading">
                  <heading>Let's do this</heading>
                </hcontainer>
              </section>
              <section id="section-304">
                <num>304.</num>
                <heading>Weirdo numbering</heading>
                <subsection id="section-304.304.1">
                  <num>304.1</num>
                  <content>
                    <p>First sub.</p>
                  </content>
                </subsection>
                <subsection id="section-304.304.2">
                  <num>304.2</num>
                  <content>
                    <p>Second sub.</p>
                  </content>
                </subsection>
                <subsection id="section-304.304.3">
                  <num>304.3</num>
                  <content>
                    <p>Third sub.</p>
                  </content>
                </subsection>
              </section>
            </part>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_6">
        <heading>Schedule 5</heading>
        <subheading>Wildlife Treaty</subheading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer id="hcontainer_1" name="crossheading">
              <heading>Introduction</heading>
            </hcontainer>
            <hcontainer id="hcontainer_2">
              <content>
                <p>sdfjhasdf;akdjsfnaksdnakdf</p>
              </content>
            </hcontainer>
            <article id="article-1">
              <num>1</num>
              <heading>Wildlife</heading>
              <hcontainer id="article-1.hcontainer_1">
                <content>
                  <p>Introductory text.</p>
                </content>
              </hcontainer>
              <paragraph id="article-1.paragraph-1">
                <num>1.</num>
                <content>
                  <p>sdkfhsdkjbfasdfb</p>
                </content>
              </paragraph>
              <paragraph id="article-1.paragraph-2">
                <num>2.</num>
                <content>
                  <p>sdkfasdkjbfakdjsbf</p>
                </content>
              </paragraph>
              <paragraph id="article-1.paragraph-3">
                <num>3.</num>
                <content>
                  <p>d;khadksjbfdkjbg</p>
                </content>
              </paragraph>
            </article>
            <article id="article-2">
              <num>2</num>
              <heading>Treaty</heading>
              <hcontainer id="article-2.hcontainer_1">
                <content>
                  <p>uygsjdfgjsdhgfsfjhsdjkfhs</p>
                  <p>fljsdhfkahsfkahsdkfhsd</p>
                  <p>sadkjfhksdjhfksdhgkhdf</p>
                  <p>sdfasdfhkadhsfkhakfhsdg</p>
                </content>
              </hcontainer>
            </article>
          </mainBody>
        </doc>
      </attachment>
    </attachments>
  </act>
</akomaNtoso>""")
        migration.migrate_document(doc)
        output = doc.doc.to_xml(pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="singleVersion">
    <meta/>
    <body/>
    <attachments>
      <attachment eId="att_1">
        <heading>Annexure</heading>
        <subheading>Things to do during lockdown</subheading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer name="crossheading" eId="hcontainer_1">
              <heading>Form A</heading>
            </hcontainer>
            <hcontainer eId="hcontainer_2">
              <content>
                <p>I ................. hereby ...............</p>
                <p>Signed</p>
              </content>
            </hcontainer>
            <hcontainer name="crossheading" eId="hcontainer_3">
              <heading>Form B</heading>
            </hcontainer>
            <hcontainer eId="hcontainer_4">
              <content>
                <p>One may:</p>
              </content>
            </hcontainer>
            <paragraph eId="para_1">
              <num>1.</num>
              <content>
                <p>Sing</p>
              </content>
            </paragraph>
            <paragraph eId="para_2">
              <num>2.</num>
              <content>
                <p>Dance</p>
              </content>
            </paragraph>
            <paragraph eId="para_3">
              <num>3.</num>
              <content>
                <p>Sway</p>
              </content>
            </paragraph>
            <hcontainer name="crossheading" eId="hcontainer_5">
              <heading>Form C</heading>
            </hcontainer>
            <section eId="sec_1">
              <num>1.</num>
              <heading>Paragraph heading</heading>
              <subsection eId="sec_1__subsec_1">
                <num>(1)</num>
                <content>
                  <p>sdfkhsdkjfhldfh.</p>
                </content>
              </subsection>
              <subsection eId="sec_1__subsec_2">
                <num>(2)</num>
                <content>
                  <p>sldfhsdkfnldksn.</p>
                </content>
              </subsection>
            </section>
            <section eId="sec_2">
              <num>2.</num>
              <heading>Another heading</heading>
              <subsection eId="sec_2__subsec_1">
                <num>(1)</num>
                <content>
                  <p>dskfahsdkfdnsv.dn.</p>
                </content>
              </subsection>
              <subsection eId="sec_2__subsec_2">
                <num>(2)</num>
                <content>
                  <p>sdfkdskvdnvmbdvmsnd.</p>
                </content>
              </subsection>
            </section>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_2">
        <heading>Schedule 1</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer eId="hcontainer_1">
              <content>
                <table eId="hcontainer_1__table_1">
                  <tr>
                    <th>
                      <p>Column 1</p>
                    </th>
                    <th>
                      <p>Column 2</p>
                    </th>
                    <th>
                      <p>Column 3</p>
                    </th>
                  </tr>
                  <tr>
                    <th>
                      <p>Sub-Council Designation</p>
                    </th>
                    <th>
                      <p>Sub-Council Name</p>
                    </th>
                    <th>
                      <p>Ward Numbers</p>
                    </th>
                  </tr>
                  <tr>
                    <td>
                      <p>1</p>
                    </td>
                    <td>
                      <p>Subcouncil 1 Blaauwberg</p>
                    </td>
                    <td>
                      <p>4, 23, 29, 32, 104, 107</p>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <p>2</p>
                    </td>
                    <td>
                      <p>Subcouncil 2 Bergdal</p>
                    </td>
                    <td>
                      <p>6, 7, 8, 111</p>
                    </td>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_3">
        <heading>Schedule 2</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer eId="hcontainer_1">
              <content>
                <table eId="hcontainer_1__table_1">
                  <tr>
                    <th>
                      <p>COLUMN 1</p>
                    </th>
                    <th>
                      <p>COLUMN 2</p>
                    </th>
                  </tr>
                  <tr>
                    <th>
                      <p>SUB-COUNCIL DESIGNATION</p>
                    </th>
                    <th>
                      <p>WARD NUMBERS</p>
                    </th>
                  </tr>
                  <tr>
                    <td>
                      <p>1</p>
                    </td>
                    <td>
                      <p>23, 29, 32 and 104</p>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <p>2</p>
                    </td>
                    <td>
                      <p>6, 7, 8, 101, 102 and 111</p>
                    </td>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_4">
        <heading>Third Schedule</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <chapter eId="chp_1">
              <num>1</num>
              <heading>The first Chapter</heading>
              <part eId="chp_1__part_1">
                <num>1</num>
                <heading>The first Part</heading>
                <paragraph eId="chp_1__part_1__para_1">
                  <num>1.</num>
                  <content>
                    <p>The first para</p>
                  </content>
                </paragraph>
                <paragraph eId="chp_1__part_1__para_2">
                  <num>2.</num>
                  <content>
                    <p>The second para</p>
                  </content>
                </paragraph>
                <paragraph eId="chp_1__part_1__para_345456">
                  <num>345456.</num>
                  <content>
                    <p>The last para</p>
                  </content>
                </paragraph>
              </part>
              <part eId="chp_1__part_2">
                <num>2</num>
                <heading>The second Part</heading>
                <paragraph eId="chp_1__part_2__para_1">
                  <num>1.</num>
                  <content>
                    <p>Starting all over again</p>
                  </content>
                </paragraph>
                <paragraph eId="chp_1__part_2__para_2">
                  <num>2.</num>
                  <content>
                    <p>Yup</p>
                  </content>
                </paragraph>
                <paragraph eId="chp_1__part_2__para_3">
                  <num>3.</num>
                  <content>
                    <p>sdflkdsjg;ndfg</p>
                  </content>
                </paragraph>
              </part>
            </chapter>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_5">
        <heading>Fourth Schedule</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <part eId="part_36">
              <num>36</num>
              <heading>Let's get nested</heading>
              <chapter eId="part_36__chp_A">
                <num>A</num>
                <heading>Nested Chapter</heading>
                <section eId="sec_1">
                  <num>1.</num>
                  <heading>fjlhsdkfh</heading>
                  <hcontainer eId="sec_1__hcontainer_1">
                    <content>
                      <p>dsjfhsdkjfhkshdf</p>
                    </content>
                  </hcontainer>
                </section>
                <section eId="sec_300">
                  <num>300.</num>
                  <heading>skdfhdkshfasd</heading>
                  <hcontainer eId="sec_300__hcontainer_1">
                    <content>
                      <p>asfjhadjslgfjsdghfjhg</p>
                    </content>
                  </hcontainer>
                </section>
              </chapter>
              <chapter eId="part_36__chp_B">
                <num>B</num>
                <heading>Still inside</heading>
                <section eId="sec_301">
                  <num>301.</num>
                  <heading>skhfdsjghfd</heading>
                  <hcontainer eId="sec_301__hcontainer_1">
                    <content>
                      <p>sdfjsdlgjlkdfjg</p>
                    </content>
                  </hcontainer>
                </section>
                <section eId="sec_302">
                  <num>302.</num>
                  <heading>dkfhdsjhgdbfhjg</heading>
                  <hcontainer eId="sec_302__hcontainer_1">
                    <content>
                      <blockList eId="sec_302__hcontainer_1__list_1">
                        <listIntroduction>And let's nest a list:</listIntroduction>
                        <item eId="sec_302__hcontainer_1__list_1__item_1">
                          <num>(1)</num>
                          <p>These ones are weird:</p>
                          <blockList eId="sec_302__hcontainer_1__list_1__item_1__list_1">
                            <listIntroduction><remark status="editorial">[editorial remark]</remark></listIntroduction>
                            <item eId="sec_302__hcontainer_1__list_1__item_1__list_1__item_a">
                              <num>(a)</num>
                              <p>sfhsdkjfhksdh;</p>
                            </item>
                            <item eId="sec_302__hcontainer_1__list_1__item_1__list_1__item_b">
                              <num>(b)</num>
                              <p>sdfhsdnfbmnsdbf;</p>
                              <p><remark status="editorial">[editorial remark]</remark></p>
                            </item>
                            <item eId="sec_302__hcontainer_1__list_1__item_1__list_1__item_c">
                              <num>(c)</num>
                              <p>jshaasbmnbxc.</p>
                            </item>
                          </blockList>
                        </item>
                        <item eId="sec_302__hcontainer_1__list_1__item_2">
                          <num>(2)</num>
                          <p>A nother not-quite subsection.</p>
                        </item>
                      </blockList>
                    </content>
                  </hcontainer>
                </section>
              </chapter>
            </part>
            <part eId="part_37">
              <num>37</num>
              <heading>Back out to the top level</heading>
              <section eId="sec_303">
                <num>303.</num>
                <heading>sfsjdbfbsdjnfb</heading>
                <subsection eId="sec_303__subsec_1">
                  <num>(1)</num>
                  <content>
                    <p>Normal subsection:</p>
                    <blockList eId="sec_303__subsec_1__list_1">
                      <listIntroduction>Normal list:</listIntroduction>
                      <item eId="sec_303__subsec_1__list_1__item_a">
                        <num>(a)</num>
                        <p>normal item;</p>
                      </item>
                      <item eId="sec_303__subsec_1__list_1__item_a">
                        <num>(a)</num>
                        <p>normal item (duplicate number);</p>
                      </item>
                      <item eId="sec_303__subsec_1__list_1__item_a">
                        <num>(a)</num>
                        <blockList eId="sec_303__subsec_1__list_1__item_a__list_1">
                          <listIntroduction>normal item (also duplicate):</listIntroduction>
                          <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_i">
                            <num>(i)</num>
                            <blockList eId="sec_303__subsec_1__list_1__item_a__list_1__item_i__list_1">
                              <listIntroduction>sublist item, plus:</listIntroduction>
                              <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_i__list_1__item_A">
                                <num>(A)</num>
                                <p>nested further!</p>
                              </item>
                              <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_i__list_1__item_B">
                                <num>(B)</num>
                                <p>nested further!</p>
                              </item>
                              <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_i__list_1__item_B">
                                <num>(B)</num>
                                <p>nested further!</p>
                              </item>
                            </blockList>
                          </item>
                          <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_ii">
                            <num>(ii)</num>
                            <p>moar; and</p>
                          </item>
                        </blockList>
                      </item>
                      <item eId="sec_303__subsec_1__list_1__item_b">
                        <num>(b)</num>
                        <p>final item.</p>
                      </item>
                    </blockList>
                  </content>
                </subsection>
                <hcontainer name="crossheading" eId="sec_303__hcontainer_1">
                  <heading>Let's do this</heading>
                </hcontainer>
              </section>
              <section eId="sec_304">
                <num>304.</num>
                <heading>Weirdo numbering</heading>
                <subsection eId="sec_304__subsec_304-1">
                  <num>304.1</num>
                  <content>
                    <p>First sub.</p>
                  </content>
                </subsection>
                <subsection eId="sec_304__subsec_304-2">
                  <num>304.2</num>
                  <content>
                    <p>Second sub.</p>
                  </content>
                </subsection>
                <subsection eId="sec_304__subsec_304-3">
                  <num>304.3</num>
                  <content>
                    <p>Third sub.</p>
                  </content>
                </subsection>
              </section>
            </part>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_6">
        <heading>Schedule 5</heading>
        <subheading>Wildlife Treaty</subheading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer name="crossheading" eId="hcontainer_1">
              <heading>Introduction</heading>
            </hcontainer>
            <hcontainer eId="hcontainer_2">
              <content>
                <p>sdfjhasdf;akdjsfnaksdnakdf</p>
              </content>
            </hcontainer>
            <article eId="article_1">
              <num>1</num>
              <heading>Wildlife</heading>
              <hcontainer eId="article_1__hcontainer_1">
                <content>
                  <p>Introductory text.</p>
                </content>
              </hcontainer>
              <paragraph eId="article_1__para_1">
                <num>1.</num>
                <content>
                  <p>sdkfhsdkjbfasdfb</p>
                </content>
              </paragraph>
              <paragraph eId="article_1__para_2">
                <num>2.</num>
                <content>
                  <p>sdkfasdkjbfakdjsbf</p>
                </content>
              </paragraph>
              <paragraph eId="article_1__para_3">
                <num>3.</num>
                <content>
                  <p>d;khadksjbfdkjbg</p>
                </content>
              </paragraph>
            </article>
            <article eId="article_2">
              <num>2</num>
              <heading>Treaty</heading>
              <hcontainer eId="article_2__hcontainer_1">
                <content>
                  <p>uygsjdfgjsdhgfsfjhsdjkfhs</p>
                  <p>fljsdhfkahsfkahsdkfhsd</p>
                  <p>sadkjfhksdjhfksdhgkhdf</p>
                  <p>sdfasdfhkadhsfkhakfhsdg</p>
                </content>
              </hcontainer>
            </article>
          </mainBody>
        </doc>
      </attachment>
    </attachments>
  </act>
</akomaNtoso>
""",
            output
        )

    def test_eid_table(self):
        """ includes checks for tables in main body and Schedules
        """
        pass

    def test_eid_terms(self):
        migration = AKNeId()
        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <section id="section-1">
        <num>1</num>
        <heading>Definitions</heading>
        <content>
          <p>a <term id="trm1">term</term> and another <term id="trm2">term2</term></p>
          <blockList id="section-1.list0">
            <item id="section-1.list0.a">
              <num>(a)</num>
              <p>a <term id="trm3">term</term> and another <term id="trm4">term2</term></p>
            </item>
            <item id="section-1.list0.b">
              <num>(b)</num>
              <p>a <term id="trm5">term</term> and another <term id="trm6">term2</term></p>
            </item>
          </blockList>
          <p>a <term id="trm7">term</term> and another <term id="trm8">term2</term></p>
        </content>
      </section>
    </body>
  </act>
</akomaNtoso>""")
        migration.migrate_document(doc)
        output = doc.doc.to_xml(pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <section eId="sec_1">
        <num>1</num>
        <heading>Definitions</heading>
        <content>
          <p>a <term eId="sec_1__term_1">term</term> and another <term eId="sec_1__term_2">term2</term></p>
          <blockList eId="sec_1__list_1">
            <item eId="sec_1__list_1__item_a">
              <num>(a)</num>
              <p>a <term eId="sec_1__list_1__item_a__term_1">term</term> and another <term eId="sec_1__list_1__item_a__term_2">term2</term></p>
            </item>
            <item eId="sec_1__list_1__item_b">
              <num>(b)</num>
              <p>a <term eId="sec_1__list_1__item_b__term_1">term</term> and another <term eId="sec_1__list_1__item_b__term_2">term2</term></p>
            </item>
          </blockList>
          <p>a <term eId="sec_1__term_3">term</term> and another <term eId="sec_1__term_4">term2</term></p>
        </content>
      </section>
    </body>
  </act>
</akomaNtoso>
""", output)

#     def test_href(self):
#         """ checks that (only) internal section references are updated
#         """
#         migration = HrefMigration()
#         doc = Document(work=self.work, document_xml="""
# <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
#   <act contains="singleVersion">
#     <meta/>
#     <body>
#       <chapter eId="chapter-VIII">
#         <num>VIII</num>
#         <heading>Emissions from compression ignition powered vehicles</heading>
#         <section eId="section-22">
#           <num>22.</num>
#           <heading>Stopping of vehicles for inspection and testing</heading>
#           <subsection eId="section-22.1">
#             <num>(1)</num>
#             <content>
#               <p>In order to enable an <term refersTo="#term-authorised_official" eId="trm264">authorised official</term> to enforce the provisions of this Chapter, the driver of a <term refersTo="#term-vehicle" eId="trm265">vehicle</term> must comply with any reasonable direction given by an authorised official to conduct or facilitate the inspection or testing of the <term refersTo="#term-vehicle" eId="trm266">vehicle</term>.</p>
#             </content>
#           </subsection>
#           <subsection eId="section-22.2">
#             <num>(2)</num>
#             <content>
#               <blockList eId="section-22.2.list0">
#                 <listIntroduction>An <term refersTo="#term-authorised_official" eId="trm267">authorised official</term> may issue an instruction to the driver of a <term refersTo="#term-vehicle" eId="trm268">vehicle</term> suspected of emitting <term refersTo="#term-dark_smoke" eId="trm269">dark smoke</term> to stop the <term refersTo="#term-vehicle" eId="trm270">vehicle</term> in order to -</listIntroduction>
#                 <item eId="section-22.2.list0.b">
#                   <num>(b)</num>
#                   <p>conduct a visual inspection of the <term refersTo="#term-vehicle" eId="trm274">vehicle</term> and, if the authorised official reasonably believes that an offence has been committed under <ref href="#section-21">section 21</ref> instruct the driver of the vehicle, who is presumed to be the owner of the vehicle unless he or she produces evidence to the contrary in writing, to take the vehicle to a specified address or testing station, within a specified period of time, for inspection and testing in accordance with <ref href="#section-23">section 23</ref>.</p>
#                 </item>
#               </blockList>
#             </content>
#           </subsection>
#         </section>
#         <section eId="section-23">
#           <num>23.</num>
#           <heading>Testing procedure</heading>
#           <subsection eId="section-23.1">
#             <num>(1)</num>
#             <content>
#               <p>An <term refersTo="#term-authorised_official" eId="trm275">authorised official</term> must use the <term refersTo="#term-free_acceleration_test" eId="trm276">free acceleration test</term> method in order to determine whether a <term refersTo="#term-compression_ignition_powered_vehicle" eId="trm277">compression ignition powered vehicle</term> is being driven or used in contravention of <ref href="#section-21">section 21</ref>(1).</p>
#             </content>
#           </subsection>
#           <subsection eId="section-23.3">
#             <num>(3)</num>
#             <content>
#               <blockList eId="section-23.3.list0">
#                 <listIntroduction>If, having conducted the <term refersTo="#term-free_acceleration_test" eId="trm293">free acceleration test</term>, the <term refersTo="#term-authorised_official" eId="trm294">authorised official</term> is satisfied that the <term refersTo="#term-vehicle" eId="trm295">vehicle</term> -</listIntroduction>
#                 <item eId="section-23.3.list0.a">
#                   <num>(a)</num>
#                   <p>is not emitting <term refersTo="#term-dark_smoke" eId="trm296">dark smoke</term>, he or she must furnish the driver of the <term refersTo="#term-vehicle" eId="trm297">vehicle</term> with a certificate indicating that the <term refersTo="#term-vehicle" eId="trm298">vehicle</term> is not being driven or used in contravention of <ref href="#section-21">section 21</ref>; or</p>
#                 </item>
#                 <item eId="section-23.3.list0.b">
#                   <num>(b)</num>
#                   <p>is emitting <term refersTo="#term-dark_smoke" eId="trm299">dark smoke</term>, he or she must issue the driver of the <term refersTo="#term-vehicle" eId="trm300">vehicle</term> with a repair notice in accordance with <ref href="#section-24">section 24</ref>.</p>
#                 </item>
#               </blockList>
#             </content>
#           </subsection>
#         </section>
#         <section eId="section-24">
#           <num>24.</num>
#           <heading>Repair notice</heading>
#           <subsection eId="section-24.1">
#             <num>(1)</num>
#             <content>
#               <p>In the event that a determination is made in terms of <ref href="#section-23">section 23</ref>(3) that a vehicle is emitting dark smoke the authorised official must instruct the owner of the vehicle in writing to repair the vehicle and present it for re-testing at the address specified in a repair notice;</p>
#             </content>
#           </subsection>
#         </section>
#       </chapter>
#     </body>
#   </act>
# </akomaNtoso>""")
#         migration.migrate_document(doc)
#         output = doc.doc.to_xml(pretty_print=True, encoding='unicode')
#         self.assertMultiLineEqual(
#             """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
#   <act contains="singleVersion">
#     <meta/>
#     <body>
#       <chapter eId="chapter-VIII">
#         <num>VIII</num>
#         <heading>Emissions from compression ignition powered vehicles</heading>
#         <section eId="section-22">
#           <num>22.</num>
#           <heading>Stopping of vehicles for inspection and testing</heading>
#           <subsection eId="section-22.1">
#             <num>(1)</num>
#             <content>
#               <p>In order to enable an <term refersTo="#term-authorised_official" eId="trm264">authorised official</term> to enforce the provisions of this Chapter, the driver of a <term refersTo="#term-vehicle" eId="trm265">vehicle</term> must comply with any reasonable direction given by an authorised official to conduct or facilitate the inspection or testing of the <term refersTo="#term-vehicle" eId="trm266">vehicle</term>.</p>
#             </content>
#           </subsection>
#           <subsection eId="section-22.2">
#             <num>(2)</num>
#             <content>
#               <blockList eId="section-22.2.list0">
#                 <listIntroduction>An <term refersTo="#term-authorised_official" eId="trm267">authorised official</term> may issue an instruction to the driver of a <term refersTo="#term-vehicle" eId="trm268">vehicle</term> suspected of emitting <term refersTo="#term-dark_smoke" eId="trm269">dark smoke</term> to stop the <term refersTo="#term-vehicle" eId="trm270">vehicle</term> in order to -</listIntroduction>
#                 <item eId="section-22.2.list0.b">
#                   <num>(b)</num>
#                   <p>conduct a visual inspection of the <term refersTo="#term-vehicle" eId="trm274">vehicle</term> and, if the authorised official reasonably believes that an offence has been committed under <ref href="#sec_21">section 21</ref> instruct the driver of the vehicle, who is presumed to be the owner of the vehicle unless he or she produces evidence to the contrary in writing, to take the vehicle to a specified address or testing station, within a specified period of time, for inspection and testing in accordance with <ref href="#sec_23">section 23</ref>.</p>
#                 </item>
#               </blockList>
#             </content>
#           </subsection>
#         </section>
#         <section eId="section-23">
#           <num>23.</num>
#           <heading>Testing procedure</heading>
#           <subsection eId="section-23.1">
#             <num>(1)</num>
#             <content>
#               <p>An <term refersTo="#term-authorised_official" eId="trm275">authorised official</term> must use the <term refersTo="#term-free_acceleration_test" eId="trm276">free acceleration test</term> method in order to determine whether a <term refersTo="#term-compression_ignition_powered_vehicle" eId="trm277">compression ignition powered vehicle</term> is being driven or used in contravention of <ref href="#sec_21">section 21</ref>(1).</p>
#             </content>
#           </subsection>
#           <subsection eId="section-23.3">
#             <num>(3)</num>
#             <content>
#               <blockList eId="section-23.3.list0">
#                 <listIntroduction>If, having conducted the <term refersTo="#term-free_acceleration_test" eId="trm293">free acceleration test</term>, the <term refersTo="#term-authorised_official" eId="trm294">authorised official</term> is satisfied that the <term refersTo="#term-vehicle" eId="trm295">vehicle</term> -</listIntroduction>
#                 <item eId="section-23.3.list0.a">
#                   <num>(a)</num>
#                   <p>is not emitting <term refersTo="#term-dark_smoke" eId="trm296">dark smoke</term>, he or she must furnish the driver of the <term refersTo="#term-vehicle" eId="trm297">vehicle</term> with a certificate indicating that the <term refersTo="#term-vehicle" eId="trm298">vehicle</term> is not being driven or used in contravention of <ref href="#sec_21">section 21</ref>; or</p>
#                 </item>
#                 <item eId="section-23.3.list0.b">
#                   <num>(b)</num>
#                   <p>is emitting <term refersTo="#term-dark_smoke" eId="trm299">dark smoke</term>, he or she must issue the driver of the <term refersTo="#term-vehicle" eId="trm300">vehicle</term> with a repair notice in accordance with <ref href="#sec_24">section 24</ref>.</p>
#                 </item>
#               </blockList>
#             </content>
#           </subsection>
#         </section>
#         <section eId="section-24">
#           <num>24.</num>
#           <heading>Repair notice</heading>
#           <subsection eId="section-24.1">
#             <num>(1)</num>
#             <content>
#               <p>In the event that a determination is made in terms of <ref href="#sec_23">section 23</ref>(3) that a vehicle is emitting dark smoke the authorised official must instruct the owner of the vehicle in writing to repair the vehicle and present it for re-testing at the address specified in a repair notice;</p>
#             </content>
#           </subsection>
#         </section>
#       </chapter>
#     </body>
#   </act>
# </akomaNtoso>
# """,
#             output
#         )
