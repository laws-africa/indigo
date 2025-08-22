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
