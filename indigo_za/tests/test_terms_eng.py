# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from lxml import etree

from indigo_api.tests.fixtures import *  # noqa
from indigo_za.terms import TermsFinderENG
from indigo_api.models import Document, Work


class TermsFinderENGTestCase(APITestCase):
    def setUp(self):
        self.work = Work(frbr_uri='/za/act/1998/1')
        self.finder = TermsFinderENG()

    def test_find_simple(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"Act" means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
      <blockList id="section-1.paragraph-0.list3">
        <listIntroduction>"authorised officer" includes-</listIntroduction>
        <item id="section-1.paragraph-0.list3.a">
          <num>(a)</num>
          <p>a person in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic Act to be an authorised officer; and</p>
        </item>
        <item id="section-1.paragraph-0.list3.b">
          <num>(b)</num>
          <p>a person appointed as an inspector by the City as contemplated in section 86 of the National Land Transport Act, 2009 (Act No. 5 of 2009);</p>
        </item>
      </blockList>
    </content>
  </paragraph>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p refersTo="#term-Act">"<def refersTo="#term-Act">Act</def>" means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
      <blockList id="section-1.paragraph-0.list3" refersTo="#term-authorised_officer">
        <listIntroduction>"<def refersTo="#term-authorised_officer">authorised officer</def>" includes-</listIntroduction>
        <item id="section-1.paragraph-0.list3.a">
          <num>(a)</num>
          <p>a person in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic <term refersTo="#term-Act" id="trm0">Act</term> to be an authorised officer; and</p>
        </item>
        <item id="section-1.paragraph-0.list3.b">
          <num>(b)</num>
          <p>a person appointed as an inspector by the City as contemplated in section 86 of the National Land Transport <term refersTo="#term-Act" id="trm1">Act</term>, 2009 (<term refersTo="#term-Act" id="trm2">Act</term> No. 5 of 2009);</p>
        </item>
      </blockList>
    </content>
  </paragraph>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True).decode('utf-8'))

    def test_find_no_heading(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section id="section-1">
  <num>1.</num>
  <heading/>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"Act" means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
      <blockList id="section-1.paragraph-0.list3">
        <listIntroduction>"authorised officer" includes-</listIntroduction>
        <item id="section-1.paragraph-0.list3.a">
          <num>(a)</num>
          <p>a person in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic Act to be an authorised officer; and</p>
        </item>
        <item id="section-1.paragraph-0.list3.b">
          <num>(b)</num>
          <p>a person appointed as an inspector by the City as contemplated in section 86 of the National Land Transport Act, 2009 (Act No. 5 of 2009);</p>
        </item>
      </blockList>
    </content>
  </paragraph>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      
<section id="section-1">
  <num>1.</num>
  <heading/>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"Act" means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
      <blockList id="section-1.paragraph-0.list3">
        <listIntroduction>"authorised officer" includes-</listIntroduction>
        <item id="section-1.paragraph-0.list3.a">
          <num>(a)</num>
          <p>a person in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic Act to be an authorised officer; and</p>
        </item>
        <item id="section-1.paragraph-0.list3.b">
          <num>(b)</num>
          <p>a person appointed as an inspector by the City as contemplated in section 86 of the National Land Transport Act, 2009 (Act No. 5 of 2009);</p>
        </item>
      </blockList>
    </content>
  </paragraph>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True).decode('utf-8'))

    def test_find_with_empty_string(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section id="section-1">
  <num>1.</num>
  <heading/>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"" means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </paragraph>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      
<section id="section-1">
  <num>1.</num>
  <heading/>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"" means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </paragraph>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True).decode('utf-8'))

    def test_unicode(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>"Actë" means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </paragraph>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p refersTo="#term-Actë">"<def refersTo="#term-Actë">Actë</def>" means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </paragraph>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_fancy_quotes(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>“Act“ means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </paragraph>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p refersTo="#term-Act">“<def refersTo="#term-Act">Act</def>“ means the National Road Traffic Act, 1996 (<ref href="/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </paragraph>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_whitespace_between_adjacent_terms(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>"fire" means a combustion;</p>
      <p>"truck" means a vehicle;</p>
    </content>
  </paragraph>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>Do not park near a fire truck.</p>
    </content>
  </paragraph>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p refersTo="#term-fire">"<def refersTo="#term-fire">fire</def>" means a combustion;</p>
      <p refersTo="#term-truck">"<def refersTo="#term-truck">truck</def>" means a vehicle;</p>
    </content>
  </paragraph>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>Do not park near a <term refersTo="#term-fire" id="trm0">fire</term> <term refersTo="#term-truck" id="trm1">truck</term>.</p>
    </content>
  </paragraph>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_whitespace_between_adjacent_terms2(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <subsection id="section-1.1">
    <num>(1)</num>
    <content>
      <p>"keep" means something</p>
      <p>"game" means something</p>
      <p>keep game or any other wild animal.</p>
      <p>may keep game or any other wild animal.</p>
      <p>may not keep game</p>
    </content>
  </subsection>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      
<section id="section-1">
  <num>1.</num>
  <heading>Definitions</heading>
  <subsection id="section-1.1">
    <num>(1)</num>
    <content>
      <p refersTo="#term-keep">"<def refersTo="#term-keep">keep</def>" means something</p>
      <p refersTo="#term-game">"<def refersTo="#term-game">game</def>" means something</p>
      <p><term refersTo="#term-keep" id="trm0">keep</term> <term refersTo="#term-game" id="trm1">game</term> or any other wild animal.</p>
      <p>may <term refersTo="#term-keep" id="trm2">keep</term> <term refersTo="#term-game" id="trm3">game</term> or any other wild animal.</p>
      <p>may not <term refersTo="#term-keep" id="trm4">keep</term> <term refersTo="#term-game" id="trm5">game</term></p>
    </content>
  </subsection>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))
