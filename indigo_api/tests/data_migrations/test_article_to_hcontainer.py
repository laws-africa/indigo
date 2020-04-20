# coding=utf-8
from django.test import TestCase
from cobalt import Act
from lxml import etree

from indigo_api.data_migrations import ScheduleArticleToHcontainer


OLD_SCHEDULE = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.akomantoso.org/2.0" xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd">
  <act contains="originalVersion">
    <meta>
      <identification source="">
        <FRBRWork>
          <FRBRthis value="/za/act/1900/1/main"/>
          <FRBRuri value="/za/act/1900/1"/>
          <FRBRalias value="Untitled"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/za/act/1900/1/eng@/main"/>
          <FRBRuri value="/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/za/act/1900/1/eng@/main"/>
          <FRBRuri value="/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
        </FRBRManifestation>
      </identification>
      <publication date="2005-07-24" name="Province of Western Cape: σπαθιοῦ Gazette" number="6277" showAs="Province of Western Cape: Provincial Gazette"/>
    </meta>
    <body>
      <paragraph>
        <content>
          <p>body</p>
        </content>
      </paragraph>
    </body>
  </act>
  <components>
    <component id="component-schedule">
      <doc name="schedule">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/za/act/1980/01/schedule"/>
              <FRBRuri value="/za/act/1980/01"/>
              <FRBRalias value="Schedule"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/za/act/1980/01/eng@/schedule"/>
              <FRBRuri value="/za/act/1980/01/eng@"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/za/act/1980/01/eng@/schedule"/>
              <FRBRuri value="/za/act/1980/01/eng@"/>
              <FRBRdate date="' + today + '" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <article id="schedule">
            %s
          </article>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>
"""

NEW_SCHEDULE = """<akomaNtoso xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.akomantoso.org/2.0" xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd">
  <act contains="originalVersion">
    <meta>
      <identification source="">
        <FRBRWork>
          <FRBRthis value="/za/act/1900/1/main"/>
          <FRBRuri value="/za/act/1900/1"/>
          <FRBRalias value="Untitled"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/za/act/1900/1/eng@/main"/>
          <FRBRuri value="/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/za/act/1900/1/eng@/main"/>
          <FRBRuri value="/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
        </FRBRManifestation>
      </identification>
      <publication date="2005-07-24" name="Province of Western Cape: σπαθιοῦ Gazette" number="6277" showAs="Province of Western Cape: Provincial Gazette"/>
    </meta>
    <body>
      <paragraph>
        <content>
          <p>body</p>
        </content>
      </paragraph>
    </body>
  </act>
  <components>
    <component id="component-schedule">
      <doc name="schedule">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/za/act/1980/01/schedule"/>
              <FRBRuri value="/za/act/1980/01"/>
              <FRBRalias value="Schedule"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/za/act/1980/01/eng@/schedule"/>
              <FRBRuri value="/za/act/1980/01/eng@"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/za/act/1980/01/eng@/schedule"/>
              <FRBRuri value="/za/act/1980/01/eng@"/>
              <FRBRdate date="' + today + '" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <hcontainer id="schedule" name="schedule">
            %s
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>
"""


class MigrationTestCase(TestCase):
    maxDiff = None

    def test_migration_with_heading(self):
        migration = ScheduleArticleToHcontainer()

        xml = OLD_SCHEDULE % ("""
        <heading>BY-LAWS REPEALED BY SECTION 99</heading>
        <paragraph id="schedule2.paragraph-0">
          <content>
            <p>None</p>
          </content>
        </paragraph>""")
        act = Act(xml)
        migration.migrate_act(act)

        expected = NEW_SCHEDULE % """
        <heading>Schedule</heading><subheading>BY-LAWS REPEALED BY SECTION 99</subheading>
        <paragraph id="schedule2.paragraph-0">
          <content>
            <p>None</p>
          </content>
        </paragraph>"""
        self.assertMultiLineEqual(
            expected,
            etree.tostring(act.root, encoding='utf-8', pretty_print=True).decode('utf-8'))

    def test_migration_without_heading(self):
        migration = ScheduleArticleToHcontainer()

        xml = OLD_SCHEDULE % ("""
        <paragraph id="schedule2.paragraph-0">
          <content>
            <p>None</p>
          </content>
        </paragraph>""")
        act = Act(xml)
        migration.migrate_act(act)

        expected = NEW_SCHEDULE % """
        <heading>Schedule</heading><paragraph id="schedule2.paragraph-0">
          <content>
            <p>None</p>
          </content>
        </paragraph>"""
        self.assertMultiLineEqual(
            expected,
            etree.tostring(act.root, encoding='utf-8', pretty_print=True).decode('utf-8'))
