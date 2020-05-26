# -*- coding: utf-8 -*

DOCUMENT_FIXTURE = """<?xml version="1.0"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta>
      <identification source="">
        <FRBRWork>
          <FRBRthis value="/akn/za/act/1900/1/!main"/>
          <FRBRuri value="/akn/za/act/1900/1"/>
          <FRBRalias value="Untitled"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za/act/1900/1/eng@/!main"/>
          <FRBRuri value="/akn/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za/act/1900/1/eng@/!main"/>
          <FRBRuri value="/akn/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
        </FRBRManifestation>
      </identification>
      <publication date="2005-07-24" name="Province of Western Cape: σπαθιοῦ Gazette" number="6277" showAs="Province of Western Cape: Provincial Gazette"/>
    </meta>
    <body>
      %s
    </body>
  </act>
</akomaNtoso>
"""

BODY_FIXTURE = """
<body>
  <section eId="sec_1">
    <content>
      <p>%s</p>
    </content>
  </section>
</body>
"""

COMPONENT_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta>
      <identification source="">
        <FRBRWork>
          <FRBRthis value="/akn/za/act/1900/1/!main"/>
          <FRBRuri value="/akn/za/act/1900/1"/>
          <FRBRalias value="Untitled"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za/act/1900/1/eng@/!main"/>
          <FRBRuri value="/akn/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za/act/1900/1/eng@/!main"/>
          <FRBRuri value="/akn/za/act/1900/1/eng@"/>
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
    <attachments>
      <attachment eId="att_1">
        <doc name="schedule">
          <meta>
            <identification source="#slaw">
              <FRBRWork>
                <FRBRthis value="/akn/za/act/1980/01/!schedule"/>
                <FRBRuri value="/akn/za/act/1980/01"/>
                <FRBRalias value="Schedule"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council"/>
                <FRBRcountry value="za"/>
              </FRBRWork>
              <FRBRExpression>
                <FRBRthis value="/akn/za/act/1980/01/eng@/!schedule"/>
                <FRBRuri value="/akn/za/act/1980/01/eng@"/>
                <FRBRdate date="1980-01-01" name="Generation"/>
                <FRBRauthor href="#council"/>
                <FRBRlanguage language="eng"/>
              </FRBRExpression>
              <FRBRManifestation>
                <FRBRthis value="/akn/za/act/1980/01/eng@/!schedule"/>
                <FRBRuri value="/akn/za/act/1980/01/eng@"/>
                <FRBRdate date="' + today + '" name="Generation"/>
                <FRBRauthor href="#slaw"/>
              </FRBRManifestation>
            </identification>
          </meta>
          <mainBody>
            %s
          </mainBody>
        </doc>
      </attachment>
    </attachments>
  </act>
</akomaNtoso>
"""


def body_fixture(text):
    return BODY_FIXTURE % text


def document_fixture(text=None, xml=None):
    if text:
        xml = """<section eId="sec_1"><content><p>%s</p></content></section>""" % text

    return DOCUMENT_FIXTURE % xml


def component_fixture(text=None, xml=None):
    if text:
        xml = """<section eId="sec_1"><content><p>%s</p></content></section>""" % text

    return COMPONENT_FIXTURE % xml
