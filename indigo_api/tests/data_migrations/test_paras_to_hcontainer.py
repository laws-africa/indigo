# coding=utf-8
from django.test import TestCase

from indigo_api.data_migrations import UnnumberedParagraphsToHcontainer
from indigo_api.models import Document, Work


class MigrationTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.work = Work(frbr_uri='/za/act/2019/1')

    def test_migration(self):
        migration = UnnumberedParagraphsToHcontainer()

        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body>
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
</akomaNtoso>
""")
        migration.migrate_document(doc)
        doc.refresh_xml()
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body>
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
</akomaNtoso>""",
            doc.document_xml)

    def test_schedules(self):
            migration = UnnumberedParagraphsToHcontainer()

            doc = Document(work=self.work, document_xml="""
    <akomaNtoso xmlns="http://www.akomantoso.org/2.0">
      <act>
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
        <component id="component-schedule3">
          <doc name="schedule3">
            <meta/>
            <mainBody>
              <hcontainer id="schedule3" name="schedule">
                <heading>Schedule 3</heading>
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
      </components>
    </akomaNtoso>
        """)
            migration.migrate_document(doc)
            doc.refresh_xml()
            self.assertMultiLineEqual(
                """<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
      <act>
        <body/>
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
                <hcontainer id="schedule1.hcontainer_2">
                  <content>
                    <p>All fuel-burning equipment using Heavy Fuel Oil or other liquid fuels with a sulphur content equal to or greater than 2.5 % by weight must be fitted with a fully insulated chimney using either a 25mm air gap or mineral wool insulation to prevent the formation of acid smut. Such chimneys must be maintained in a good state of repair at all times.</p>
                  </content>
                </hcontainer>
                <hcontainer id="schedule1.crossheading-1" name="crossheading">
                  <heading>Wood-fired pizza ovens and other solid fuel combustion equipment:</heading>
                </hcontainer>
                <hcontainer id="schedule1.hcontainer_2">
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
