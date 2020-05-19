# coding=utf-8
from django.test import TestCase

from indigo_api.data_migrations import ComponentSchedulesToAttachments
from indigo_api.models import Work, Document


class MigrationTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.work = Work(frbr_uri='/za/act/2019/1')

    def test_migration_heading_subheading(self):
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
</akomaNtoso>
    """)
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
