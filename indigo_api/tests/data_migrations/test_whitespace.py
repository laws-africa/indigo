# coding=utf-8
from django.test import TestCase

from indigo_api.data_migrations import FixSignificantWhitespace


FIXTURE = """<akomaNtoso xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.akomantoso.org/2.0" xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd">
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
      <publication date="2005-07-24" name="Province of Western Cape: Gazette" number="6277" showAs="Province of Western Cape: Provincial Gazette"/>
    </meta>
    <body>
      %s
    </body>
  </act>
</akomaNtoso>
"""


class MigrationTestCase(TestCase):
    maxDiff = None

    def test_migration_with_heading(self):
        migration = FixSignificantWhitespace()

        input = FIXTURE % """
    <section id="section-1AA">
    <num>1AA.</num>
    <heading>
      <remark>something</remark>
    </heading>
    <subheading>
      <remark>something</remark>
    </subheading>
    <paragraph id="section-1AA.paragraph0">
      <content>
        <p> <b>remains the same</b>  </p>
        <p>
          significant
        </p>
        <p>
          <remark status="editorial">[remark]</remark>
        </p>
        <listIntroduction>
          <img src="foo" />
        </listIntroduction>
      </content>
    </paragraph>
    </section>"""

        self.assertMultiLineEqual(
            FIXTURE % """
    <section id="section-1AA">
    <num>1AA.</num>
    <heading><remark>something</remark></heading>
    <subheading><remark>something</remark></subheading>
    <paragraph id="section-1AA.paragraph0">
      <content>
        <p> <b>remains the same</b>  </p>
        <p>
          significant</p>
        <p><remark status="editorial">[remark]</remark></p>
        <listIntroduction><img src="foo" /></listIntroduction>
      </content>
    </paragraph>
    </section>""",
            migration.strip_whitespace(input)
        )

