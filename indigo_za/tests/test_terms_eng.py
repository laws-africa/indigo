from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from lxml import etree

from indigo_api.tests.fixtures import *  # noqa
from indigo_za.terms import TermsFinderENG
from indigo_api.models import Document, Work


class TermsFinderENGTestCase(APITestCase):
    def setUp(self):
        self.work = Work(frbr_uri='/akn/za/act/1998/1')
        self.finder = TermsFinderENG()

    def test_find_simple(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>In this 'By-law', unless the context indicates otherwise-</p>
      <p> "Act" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
      <blockList eId="sec_1__hcontainer_1__list_3">
        <listIntroduction>"authorised officer" includes-</listIntroduction>
        <item eId="sec_1__hcontainer_1__list_3__item_a">
          <num>(a)</num>
          <p>a "person" in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic Act to be an authorised officer; and</p>
        </item>
        <item eId="sec_1__hcontainer_1__list_3__item_b">
          <num>(b)</num>
          <p>a "person" appointed as an inspector by the City as contemplated in section 86 of the National Land Transport Act, 2009 (Act No. 5 of 2009);</p>
        </item>
      </blockList>
    </content>
  </hcontainer>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p eId="sec_1__hcontainer_1__p_1">In this 'By-law', unless the context indicates otherwise-</p>
      <blockContainer refersTo="#term-Act" class="definition" eId="sec_1__hcontainer_1__blockContainer_1"><p eId="sec_1__hcontainer_1__blockContainer_1__p_1"> "<def refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_1__p_1__def_1">Act</def>" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93" eId="sec_1__hcontainer_1__blockContainer_1__p_1__ref_1">Act No. 93 of 1996</ref>);</p>
      </blockContainer><blockContainer refersTo="#term-authorised_officer" class="definition" eId="sec_1__hcontainer_1__blockContainer_2"><blockList eId="sec_1__hcontainer_1__blockContainer_2__list_1">
        <listIntroduction eId="sec_1__hcontainer_1__blockContainer_2__list_1__intro_1">"<def refersTo="#term-authorised_officer" eId="sec_1__hcontainer_1__blockContainer_2__list_1__intro_1__def_1">authorised officer</def>" includes-</listIntroduction>
        <item eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_a">
          <num>(a)</num>
          <p eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_a__p_1">a "person" in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic <term refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_a__p_1__term_1">Act</term> to be an authorised officer; and</p>
        </item>
        <item eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_b">
          <num>(b)</num>
          <p eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_b__p_1">a "person" appointed as an inspector by the City as contemplated in section 86 of the National Land Transport <term refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_b__p_1__term_1">Act</term>, 2009 (<term refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_b__p_1__term_2">Act</term> No. 5 of 2009);</p>
        </item>
      </blockList>
    </blockContainer></content>
  </hcontainer>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True).decode('utf-8'))

    def test_find_no_heading(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading/>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"Act" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
      <blockList eId="sec_1__hcontainer_1__list_3">
        <listIntroduction>"authorised officer" includes-</listIntroduction>
        <item eId="sec_1__hcontainer_1__list_3__item_a">
          <num>(a)</num>
          <p>a person in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic Act to be an authorised officer; and</p>
        </item>
        <item eId="sec_1__hcontainer_1__list_3__item_b">
          <num>(b)</num>
          <p>a person appointed as an inspector by the City as contemplated in section 86 of the National Land Transport Act, 2009 (Act No. 5 of 2009);</p>
        </item>
      </blockList>
    </content>
  </hcontainer>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading/>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"Act" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
      <blockList eId="sec_1__hcontainer_1__list_3">
        <listIntroduction>"authorised officer" includes-</listIntroduction>
        <item eId="sec_1__hcontainer_1__list_3__item_a">
          <num>(a)</num>
          <p>a person in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic Act to be an authorised officer; and</p>
        </item>
        <item eId="sec_1__hcontainer_1__list_3__item_b">
          <num>(b)</num>
          <p>a person appointed as an inspector by the City as contemplated in section 86 of the National Land Transport Act, 2009 (Act No. 5 of 2009);</p>
        </item>
      </blockList>
    </content>
  </hcontainer>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True).decode('utf-8'))

    def test_find_with_empty_string(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading/>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </hcontainer>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading/>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </hcontainer>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True).decode('utf-8'))

    def test_unicode(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>"Actë" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </hcontainer>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <blockContainer refersTo="#term-Actë" class="definition" eId="sec_1__hcontainer_1__blockContainer_1"><p eId="sec_1__hcontainer_1__blockContainer_1__p_1">"<def refersTo="#term-Actë" eId="sec_1__hcontainer_1__blockContainer_1__p_1__def_1">Actë</def>" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93" eId="sec_1__hcontainer_1__blockContainer_1__p_1__ref_1">Act No. 93 of 1996</ref>);</p>
    </blockContainer></content>
  </hcontainer>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_fancy_quotes(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>“Act” means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </hcontainer>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <blockContainer refersTo="#term-Act" class="definition" eId="sec_1__hcontainer_1__blockContainer_1"><p eId="sec_1__hcontainer_1__blockContainer_1__p_1">“<def refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_1__p_1__def_1">Act</def>” means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93" eId="sec_1__hcontainer_1__blockContainer_1__p_1__ref_1">Act No. 93 of 1996</ref>);</p>
    </blockContainer></content>
  </hcontainer>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_fancy_quotes2(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p> ‘Act’ means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </hcontainer>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <blockContainer refersTo="#term-Act" class="definition" eId="sec_1__hcontainer_1__blockContainer_1"><p eId="sec_1__hcontainer_1__blockContainer_1__p_1"> ‘<def refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_1__p_1__def_1">Act</def>’ means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93" eId="sec_1__hcontainer_1__blockContainer_1__p_1__ref_1">Act No. 93 of 1996</ref>);</p>
    </blockContainer></content>
  </hcontainer>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_fancy_quotes3(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>«Act» means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </hcontainer>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <blockContainer refersTo="#term-Act" class="definition" eId="sec_1__hcontainer_1__blockContainer_1"><p eId="sec_1__hcontainer_1__blockContainer_1__p_1">«<def refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_1__p_1__def_1">Act</def>» means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93" eId="sec_1__hcontainer_1__blockContainer_1__p_1__ref_1">Act No. 93 of 1996</ref>);</p>
    </blockContainer></content>
  </hcontainer>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_mixed_quotes(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<article eId="art_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="art_1__hcontainer_1">
    <content>
      <p>"Women’s Police Network Sub-sub Committee" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
    </content>
  </hcontainer>
</article>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<article eId="art_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="art_1__hcontainer_1">
    <content>
      <blockContainer refersTo="#term-Women_s_Police_Network_Sub_sub_Committee" class="definition" eId="art_1__hcontainer_1__blockContainer_1"><p eId="art_1__hcontainer_1__blockContainer_1__p_1">"<def refersTo="#term-Women_s_Police_Network_Sub_sub_Committee" eId="art_1__hcontainer_1__blockContainer_1__p_1__def_1">Women’s Police Network Sub-sub Committee</def>" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93" eId="art_1__hcontainer_1__blockContainer_1__p_1__ref_1">Act No. 93 of 1996</ref>);</p>
    </blockContainer></content>
  </hcontainer>
</article>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_whitespace_between_adjacent_terms(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>"fire" means a combustion;</p>
      <p>"truck" means a vehicle;</p>
    </content>
  </hcontainer>
  <hcontainer eId="sec_1__hcontainer_2">
    <content>
      <p>Do not park near a fire truck.</p>
    </content>
  </hcontainer>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <blockContainer refersTo="#term-fire" class="definition" eId="sec_1__hcontainer_1__blockContainer_1"><p eId="sec_1__hcontainer_1__blockContainer_1__p_1">"<def refersTo="#term-fire" eId="sec_1__hcontainer_1__blockContainer_1__p_1__def_1">fire</def>" means a combustion;</p>
      </blockContainer><blockContainer refersTo="#term-truck" class="definition" eId="sec_1__hcontainer_1__blockContainer_2"><p eId="sec_1__hcontainer_1__blockContainer_2__p_1">"<def refersTo="#term-truck" eId="sec_1__hcontainer_1__blockContainer_2__p_1__def_1">truck</def>" means a vehicle;</p>
    </blockContainer></content>
  </hcontainer>
  <hcontainer eId="sec_1__hcontainer_2">
    <content>
      <p eId="sec_1__hcontainer_2__p_1">Do not park near a <term refersTo="#term-fire" eId="sec_1__hcontainer_2__p_1__term_1">fire</term> <term refersTo="#term-truck" eId="sec_1__hcontainer_2__p_1__term_2">truck</term>.</p>
    </content>
  </hcontainer>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_whitespace_between_adjacent_terms2(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <subsection eId="sec_1__subsec_1">
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
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <subsection eId="sec_1__subsec_1">
    <num>(1)</num>
    <content>
      <blockContainer refersTo="#term-keep" class="definition" eId="sec_1__subsec_1__blockContainer_1"><p eId="sec_1__subsec_1__blockContainer_1__p_1">"<def refersTo="#term-keep" eId="sec_1__subsec_1__blockContainer_1__p_1__def_1">keep</def>" means something</p>
      </blockContainer><blockContainer refersTo="#term-game" class="definition" eId="sec_1__subsec_1__blockContainer_2"><p eId="sec_1__subsec_1__blockContainer_2__p_1">"<def refersTo="#term-game" eId="sec_1__subsec_1__blockContainer_2__p_1__def_1">game</def>" means something</p>
      </blockContainer><p eId="sec_1__subsec_1__p_1"><term refersTo="#term-keep" eId="sec_1__subsec_1__p_1__term_1">keep</term> <term refersTo="#term-game" eId="sec_1__subsec_1__p_1__term_2">game</term> or any other wild animal.</p>
      <p eId="sec_1__subsec_1__p_2">may <term refersTo="#term-keep" eId="sec_1__subsec_1__p_2__term_1">keep</term> <term refersTo="#term-game" eId="sec_1__subsec_1__p_2__term_2">game</term> or any other wild animal.</p>
      <p eId="sec_1__subsec_1__p_3">may not <term refersTo="#term-keep" eId="sec_1__subsec_1__p_3__term_1">keep</term> <term refersTo="#term-game" eId="sec_1__subsec_1__p_3__term_2">game</term></p>
    </content>
  </subsection>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='UTF-8').decode('utf-8'))

    def test_heading_re(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading>Short title and interpretation</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p>In this By-law, unless the context indicates otherwise-</p>
      <p>"Act" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93">Act No. 93 of 1996</ref>);</p>
      <blockList eId="sec_1__hcontainer_1__list_3">
        <listIntroduction>"authorised officer" includes-</listIntroduction>
        <item eId="sec_1__hcontainer_1__list_3__item_a">
          <num>(a)</num>
          <p>a person in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic Act to be an authorised officer; and</p>
        </item>
        <item eId="sec_1__hcontainer_1__list_3__item_b">
          <num>(b)</num>
          <p>a person appointed as an inspector by the City as contemplated in section 86 of the National Land Transport Act, 2009 (Act No. 5 of 2009);</p>
        </item>
      </blockList>
    </content>
  </hcontainer>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading>Short title and interpretation</heading>
  <hcontainer eId="sec_1__hcontainer_1">
    <content>
      <p eId="sec_1__hcontainer_1__p_1">In this By-law, unless the context indicates otherwise-</p>
      <blockContainer refersTo="#term-Act" class="definition" eId="sec_1__hcontainer_1__blockContainer_1"><p eId="sec_1__hcontainer_1__blockContainer_1__p_1">"<def refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_1__p_1__def_1">Act</def>" means the National Road Traffic Act, 1996 (<ref href="/akn/za/act/1996/93" eId="sec_1__hcontainer_1__blockContainer_1__p_1__ref_1">Act No. 93 of 1996</ref>);</p>
      </blockContainer><blockContainer refersTo="#term-authorised_officer" class="definition" eId="sec_1__hcontainer_1__blockContainer_2"><blockList eId="sec_1__hcontainer_1__blockContainer_2__list_1">
        <listIntroduction eId="sec_1__hcontainer_1__blockContainer_2__list_1__intro_1">"<def refersTo="#term-authorised_officer" eId="sec_1__hcontainer_1__blockContainer_2__list_1__intro_1__def_1">authorised officer</def>" includes-</listIntroduction>
        <item eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_a">
          <num>(a)</num>
          <p eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_a__p_1">a person in the service of the City whose duty is to inspect licences, examine vehicles, examine driving licences, or who is a traffic officer or a road traffic law enforcement officer, and also any other person declared by the Minister of Transport by regulation made in terms of the National Road Traffic <term refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_a__p_1__term_1">Act</term> to be an authorised officer; and</p>
        </item>
        <item eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_b">
          <num>(b)</num>
          <p eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_b__p_1">a person appointed as an inspector by the City as contemplated in section 86 of the National Land Transport <term refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_b__p_1__term_1">Act</term>, 2009 (<term refersTo="#term-Act" eId="sec_1__hcontainer_1__blockContainer_2__list_1__item_b__p_1__term_2">Act</term> No. 5 of 2009);</p>
        </item>
      </blockList>
    </blockContainer></content>
  </hcontainer>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True).decode('utf-8'))

    def test_no_term_in_def(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <content>
    <blockContainer refersTo="#term-air_pollutant" class="definition" eId="sec_1__blockContainer_1">
      <p eId="sec_1__blockContainer_1__p_1">"<def refersTo="#term-air_pollutant" eId="sec_1__blockContainer_1__p_1__def_1">air pollutant</def>" includes any dust, smoke, fumes or gas that causes or may cause air pollution;</p>
    </blockContainer>
    <blockContainer refersTo="#term-air_pollution" class="definition" eId="sec_1__blockContainer_2">
      <p eId="sec_1__blockContainer_2__p_1">"<def refersTo="#term-air_pollution" eId="sec_1__blockContainer_2__p_1__def_1">air pollution</def>"</p>
    </blockContainer>
    <blockContainer refersTo="#term-dust" class="definition" eId="sec_1__blockContainer_3">
      <p eId="sec_1__blockContainer_3__p_1">"<def refersTo="#term-dust" eId="sec_1__blockContainer_3__p_1__def_1">dust</def>"</p>
    </blockContainer>
    <blockContainer refersTo="#term-smoke" class="definition" eId="sec_1__blockContainer_4">
      <p eId="sec_1__blockContainer_4__p_1">"<def refersTo="#term-smoke" eId="sec_1__blockContainer_4__p_1__def_1">smoke</def>"</p>
    </blockContainer>
  </content>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_1">
  <num>1.</num>
  <heading>Definitions</heading>
  <content>
    <blockContainer refersTo="#term-air_pollutant" class="definition" eId="sec_1__blockContainer_1">
      <p eId="sec_1__blockContainer_1__p_1">"<def refersTo="#term-air_pollutant" eId="sec_1__blockContainer_1__p_1__def_1">air pollutant</def>" includes any <term refersTo="#term-dust" eId="sec_1__blockContainer_1__p_1__term_1">dust</term>, <term refersTo="#term-smoke" eId="sec_1__blockContainer_1__p_1__term_2">smoke</term>, fumes or gas that causes or may cause <term refersTo="#term-air_pollution" eId="sec_1__blockContainer_1__p_1__term_3">air pollution</term>;</p>
    </blockContainer>
    <blockContainer refersTo="#term-air_pollution" class="definition" eId="sec_1__blockContainer_2">
      <p eId="sec_1__blockContainer_2__p_1">"<def refersTo="#term-air_pollution" eId="sec_1__blockContainer_2__p_1__def_1">air pollution</def>"</p>
    </blockContainer>
    <blockContainer refersTo="#term-dust" class="definition" eId="sec_1__blockContainer_3">
      <p eId="sec_1__blockContainer_3__p_1">"<def refersTo="#term-dust" eId="sec_1__blockContainer_3__p_1__def_1">dust</def>"</p>
    </blockContainer>
    <blockContainer refersTo="#term-smoke" class="definition" eId="sec_1__blockContainer_4">
      <p eId="sec_1__blockContainer_4__p_1">"<def refersTo="#term-smoke" eId="sec_1__blockContainer_4__p_1__def_1">smoke</def>"</p>
    </blockContainer>
  </content>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True).decode('utf-8'))

    def test_definition_sections_simple(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<chapter eId="chp_1">
  <num>1</num>
  <heading>Interpretation and objects</heading>
  <section eId="chp_1__sec_1">
    <num>1.</num>
    <heading>Definitions</heading>
  </section>
  <section eId="chp_1__sec_2">
    <num>2.</num>
    <heading>Objects of Act</heading>
  </section>
  <section eId="chp_1__sec_3">
    <num>3.</num>
    <heading>Application of Act</heading>
  </section>
</chapter>
<chapter eId="chp_2">
  <num>2</num>
  <heading>Agricultural land management</heading>
  <section eId="chp_2__sec_4">
    <num>4.</num>
    <heading>Principles</heading>
  </section>
  <section eId="chp_2__sec_5">
    <num>5.</num>
    <heading>Agricultural land evaluation and classification</heading>
  </section>
  <part eId="chp_2__part_3">
    <num>3</num>
    <heading>Provincial agricultural sector plans</heading>
    <section eId="chp_2__part_3__sec_6">
      <num>6.</num>
      <heading>Preparation of provincial agricultural sector plans</heading>
    </section>
    <section eId="chp_2__part_3__sec_7">
      <num>7.</num>
      <heading>Purpose of provincial agricultural sector plans</heading>
    </section>
  </part>
</chapter>"""))

        self.maxDiff = None
        root = etree.fromstring(doc.content.encode('utf-8'))
        self.finder.setup(root)
        self.assertEqual(['chp_1__sec_1', 'chp_1'], [(section.get('eId')) for section in self.finder.definition_sections(root)])

    def test_definition_sections_block_containers(self):
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_23N">
  <num>23N.</num>
  <heading>Limitation of <term refersTo="#term-interest" eId="sec_23N__term_1">interest</term> deductions in respect of reorganisation and acquisition transactions</heading>
  <subsection eId="sec_23N__subsec_1">
    <num>(1)</num>
    <content>
      <p eId="sec_23N__subsec_1__p_1">For the purposes of this section—</p>
      <blockContainer refersTo="#term-acquired_company" class="definition" eId="sec_23N__subsec_1__blockContainer_1">
        <blockList eId="sec_23N__subsec_1__blockContainer_1__list_1">
          <listIntroduction eId="sec_23N__subsec_1__blockContainer_1__list_1__intro_1">“<def refersTo="#term-acquired_company" eId="sec_23N__subsec_1__blockContainer_1__list_1__intro_1__def_1">acquired company</def>” means—</listIntroduction>
          <item eId="sec_23N__subsec_1__blockContainer_1__list_1__item_a">
            <num>(a)</num>
            <p eId="sec_23N__subsec_1__blockContainer_1__list_1__item_a__p_1">a transferor <term refersTo="#term-company" eId="sec_23N__subsec_1__blockContainer_1__list_1__item_a__p_1__term_1">company</term> or a liquidating <term refersTo="#term-company" eId="sec_23N__subsec_1__blockContainer_1__list_1__item_a__p_1__term_2">company</term> that disposes of assets pursuant to a <term refersTo="#term-reorganisation_transaction" eId="sec_23N__subsec_1__blockContainer_1__list_1__item_a__p_1__term_3">reorganisation transaction</term>; or</p>
          </item>
          <item eId="sec_23N__subsec_1__blockContainer_1__list_1__item_b">
            <num>(b)</num>
            <p eId="sec_23N__subsec_1__blockContainer_1__list_1__item_b__p_1">a <term refersTo="#term-company" eId="sec_23N__subsec_1__blockContainer_1__list_1__item_b__p_1__term_1">company</term> in which equity shares are acquired by another <term refersTo="#term-company" eId="sec_23N__subsec_1__blockContainer_1__list_1__item_b__p_1__term_2">company</term> in terms of an <term refersTo="#term-acquisition_transaction" eId="sec_23N__subsec_1__blockContainer_1__list_1__item_b__p_1__term_3">acquisition transaction</term>;</p>
          </item>
        </blockList>
      </blockContainer>
    </content>
  </subsection>
  <subsection eId="sec_23N__subsec_4">
    <num>(4)</num>
    <intro>
      <p eId="sec_23N__subsec_4__intro__p_1">The percentage contemplated in subsection <ref href="#chp_II__part_I__sec_23N__subsec_3__para_b" eId="sec_23N__subsec_4__intro__p_1__ref_1">(3)(b)</ref> must be determined in accordance with the formula—</p>
      <p eId="sec_23N__subsec_4__intro__p_2">in which formula—</p>
    </intro>
    <paragraph eId="sec_23N__subsec_4__para_a">
      <num>(a)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_a__p_1">“A” represents the percentage to be determined;</p>
      </content>
    </paragraph>
    <paragraph eId="sec_23N__subsec_4__para_b">
      <num>(b)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_b__p_1">“B” represents the number 40;</p>
      </content>
    </paragraph>
    <paragraph eId="sec_23N__subsec_4__para_c">
      <num>(c)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_c__p_1">“C” represents the <term refersTo="#term-average_repo_rate" eId="sec_23N__subsec_4__para_c__p_1__term_1">average repo rate</term> plus 400 basis points; and</p>
      </content>
    </paragraph>
    <paragraph eId="sec_23N__subsec_4__para_d">
      <num>(d)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_d__p_1">“D” represents the number 10,</p>
      </content>
    </paragraph>
    <wrapUp>
      <p eId="sec_23N__subsec_4__wrapup__p_1">but not exceeding 60 per cent of the <term refersTo="#term-adjusted_taxable_income" eId="sec_23N__subsec_4__wrapup__p_1__term_1">adjusted taxable income</term> of that <term refersTo="#term-acquiring_company" eId="sec_23N__subsec_4__wrapup__p_1__term_2">acquiring company</term>.</p>
    </wrapUp>
  </subsection>
  <subsection eId="sec_23N__subsec_5">
    <num>(5)</num>
    <content>
      <p eId="sec_23N__subsec_5__p_1"><remark status="editorial">[subsection <ref href="#chp_II__part_I__sec_23N__subsec_5" eId="sec_23N__subsec_5__p_1__ref_1">(5)</ref> deleted by section 42(1)(d) of <ref href="/akn/za/act/2018/23" eId="sec_23N__subsec_5__p_1__ref_2">Act 23 of 2018</ref>; effective date 1 January 2019, applicable in respect of amounts incurred on or after that date]</remark></p>
    </content>
  </subsection>
</section>"""))

        self.maxDiff = None
        root = etree.fromstring(doc.content.encode('utf-8'))
        self.finder.setup(root)
        self.assertEqual(['sec_23N__subsec_1'], [(section.get('eId')) for section in self.finder.definition_sections(root)])

    def test_find_block_containers_not_sibling_elements(self):
        """ If section 23N(1) explicitly contains definitions
            because it has one or more <blockContainer class="definition"> descendants,
            don't also mark up 'terms' in section 23N(4). Anything else in subsection (1) is fair game though.
        """
        doc = Document(work=self.work, content=document_fixture(xml="""
<section eId="sec_23N">
  <num>23N.</num>
  <heading>Limitation of interest deductions in respect of reorganisation and acquisition transactions</heading>
  <subsection eId="sec_23N__subsec_1">
    <num>(1)</num>
    <content>
      <p eId="sec_23N__subsec_1__p_1">For the purposes of this section—</p>
      <blockContainer class="definition" eId="sec_23N__subsec_1__blockContainer_1">
        <p eId="sec_23N__subsec_1__blockContainer_1__p_1">“average repo rate” in relation to a year of assessment means the average of all ruling repo rates determined by using the daily repo rates during that year of assessment;</p>
      </blockContainer>
    </content>
  </subsection>
  <subsection eId="sec_23N__subsec_4">
    <num>(4)</num>
    <intro>
      <p eId="sec_23N__subsec_4__intro__p_1">The percentage contemplated in subsection (3)(b) must be determined in accordance with the formula—</p>
      <p eId="sec_23N__subsec_4__intro__p_2">in which formula—</p>
    </intro>
    <paragraph eId="sec_23N__subsec_4__para_a">
      <num>(a)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_a__p_1">“A” represents the percentage to be determined;</p>
      </content>
    </paragraph>
    <paragraph eId="sec_23N__subsec_4__para_b">
      <num>(b)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_b__p_1">“B” represents the number 40;</p>
      </content>
    </paragraph>
    <paragraph eId="sec_23N__subsec_4__para_c">
      <num>(c)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_c__p_1">“C” represents the average repo rate plus 400 basis points; and</p>
      </content>
    </paragraph>
    <paragraph eId="sec_23N__subsec_4__para_d">
      <num>(d)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_d__p_1">“D” represents the number 10,</p>
      </content>
    </paragraph>
    <wrapUp>
      <p eId="sec_23N__subsec_4__wrapup__p_1">but not exceeding 60 per cent of the adjusted taxable income of that acquiring company.</p>
    </wrapUp>
  </subsection>
</section>"""))

        self.maxDiff = None
        self.finder.find_terms_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      
<section eId="sec_23N">
  <num>23N.</num>
  <heading>Limitation of interest deductions in respect of reorganisation and acquisition transactions</heading>
  <subsection eId="sec_23N__subsec_1">
    <num>(1)</num>
    <content>
      <p eId="sec_23N__subsec_1__p_1">For the purposes of this section—</p>
      <blockContainer class="definition" eId="sec_23N__subsec_1__blockContainer_1" refersTo="#term-average_repo_rate">
        <p eId="sec_23N__subsec_1__blockContainer_1__p_1">“<def refersTo="#term-average_repo_rate" eId="sec_23N__subsec_1__blockContainer_1__p_1__def_1">average repo rate</def>” in relation to a year of assessment means the average of all ruling repo rates determined by using the daily repo rates during that year of assessment;</p>
      </blockContainer>
    </content>
  </subsection>
  <subsection eId="sec_23N__subsec_4">
    <num>(4)</num>
    <intro>
      <p eId="sec_23N__subsec_4__intro__p_1">The percentage contemplated in subsection (3)(b) must be determined in accordance with the formula—</p>
      <p eId="sec_23N__subsec_4__intro__p_2">in which formula—</p>
    </intro>
    <paragraph eId="sec_23N__subsec_4__para_a">
      <num>(a)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_a__p_1">“A” represents the percentage to be determined;</p>
      </content>
    </paragraph>
    <paragraph eId="sec_23N__subsec_4__para_b">
      <num>(b)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_b__p_1">“B” represents the number 40;</p>
      </content>
    </paragraph>
    <paragraph eId="sec_23N__subsec_4__para_c">
      <num>(c)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_c__p_1">“C” represents the <term refersTo="#term-average_repo_rate" eId="sec_23N__subsec_4__para_c__p_1__term_1">average repo rate</term> plus 400 basis points; and</p>
      </content>
    </paragraph>
    <paragraph eId="sec_23N__subsec_4__para_d">
      <num>(d)</num>
      <content>
        <p eId="sec_23N__subsec_4__para_d__p_1">“D” represents the number 10,</p>
      </content>
    </paragraph>
    <wrapUp>
      <p eId="sec_23N__subsec_4__wrapup__p_1">but not exceeding 60 per cent of the adjusted taxable income of that acquiring company.</p>
    </wrapUp>
  </subsection>
</section>
    </body>
  
''', etree.tostring(doc.doc.body, pretty_print=True, encoding='unicode'))
