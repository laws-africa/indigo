# -*- coding: utf-8 -*

DOCUMENT_FIXTURE = u"""<?xml version="1.0" encoding="UTF-8"?>
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
      %s
    </body>
  </act>
</akomaNtoso>
"""

BODY_FIXTURE = u"""
<body>
  <section id="section-1">
    <content>
      <p>%s</p>
    </content>
  </section>
</body>
"""


def body_fixture(text):
    return BODY_FIXTURE % text


def document_fixture(text=None, xml=None):
    if text:
        xml = u"""
        <section id="section-1"><content><p>%s</p></content></section>
        """ % text

    return DOCUMENT_FIXTURE % xml
