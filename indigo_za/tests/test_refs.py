# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from lxml import etree

from indigo_api.tests.fixtures import *  # noqa
from indigo_za.refs import RefsFinderENG, RefsFinderAFR
from indigo_api.models import Document


class RefsFinderENGTestCase(APITestCase):
    def setUp(self):
        self.finder = RefsFinderENG()

    def test_find_simple(self):
        doc = Document(content=document_fixture(xml=u"""
<section id="section-1">
  <num>1.</num>
  <heading>Tester</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>Something to do with Act no 22 of 2012.</p>
      <p>And another thing about Act 4 of 1998.</p>
    </content>
  </paragraph>
</section>
        """))

        self.finder.find_references_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <section id="section-1">
    <num>1.</num>
    <heading>Tester</heading>
    <paragraph id="section-1.paragraph-0">
      <content>
        <p>Something to do with <ref href="/za/act/2012/22">Act no 22 of 2012</ref>.</p>
        <p>And another thing about <ref href="/za/act/1998/4">Act 4 of 1998</ref>.</p>
      </content>
    </paragraph>
  </section>
</body>
''', etree.tostring(doc.doc.body, pretty_print=True))

    def test_find_multiple_in_tail(self):
        doc = Document(content=document_fixture(xml=u"""
<section id="section-1">
  <num>1.</num>
  <heading>Tester</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>Something Act 4 of 2000 and "<term>City</term>" means the (Act No. 117 of 1998) and also Act 5 of 2020;</p>
    </content>
  </paragraph>
</section>
        """))

        self.finder.find_references_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <section id="section-1">
    <num>1.</num>
    <heading>Tester</heading>
    <paragraph id="section-1.paragraph-0">
      <content>
        <p>Something <ref href="/za/act/2000/4">Act 4 of 2000</ref> and "<term>City</term>" means the (<ref href="/za/act/1998/117">Act No. 117 of 1998</ref>) and also <ref href="/za/act/2020/5">Act 5 of 2020</ref>;</p>
      </content>
    </paragraph>
  </section>
</body>
''', etree.tostring(doc.doc.body, pretty_print=True))

    def test_ignore_existing(self):
        doc = Document(content=document_fixture(xml=u"""
<section id="section-1">
  <num>1.</num>
  <heading>Tester</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>Something to do with <ref href="/za/act/2012/22">Act no 22 of 2012</ref>.</p>
      <p>And another thing about <ref href="/za/act/1998/4"><b>Act 4 of 1998</b></ref>.</p>
    </content>
  </paragraph>
</section>
        """))

        self.finder.find_references_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <section id="section-1">
    <num>1.</num>
    <heading>Tester</heading>
    <paragraph id="section-1.paragraph-0">
      <content>
        <p>Something to do with <ref href="/za/act/2012/22">Act no 22 of 2012</ref>.</p>
        <p>And another thing about <ref href="/za/act/1998/4"><b>Act 4 of 1998</b></ref>.</p>
      </content>
    </paragraph>
  </section>
</body>
''', etree.tostring(doc.doc.body, pretty_print=True))

    def test_constitution(self):
        doc = Document(content=document_fixture(xml=u"""
<section id="section-1">
  <num>1.</num>
  <heading>Tester</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>the Constitution</p>
      <p>the Constitution, 1996</p>
      <p>the Constitution of South Africa</p>
      <p>the Constitution of the Republic of South Africa</p>
      <p>the Constitution of the Republic of South Africa, 1996</p>
      <p>the Constitution of the Republic of South Africa 1996</p>
      <p>the Constitution of the Republic of South Africa Act, 1996</p>
      <p>the Constitution of the Republic of South Africa, 1996 ( Act 108 of 1996 )</p>
      <p>the Constitution of the Republic of South Africa, 1996 ( Act No 108 of 1996 )</p>
      <p>the Constitution of the Republic of South Africa, 1996 ( Act No. 108 of 1996 )</p>
      <p>the Constitution of the Republic of South Africa Act, 1996 ( Act No. 108 of 1996 )</p>
      <p>the Constitution of the Republic of South Africa  Act 108 of 1996</p>
      <p>the Constitution of the Republic of South Africa (Act 108 of 1996)</p>
      <p>the below shouldn't match</p>
      <p>Constitutionally unsound</p>
      <p>is unconstitutional</p>
      <p>their constitution is poor</p>
    </content>
  </paragraph>
</section>
        """))

        self.finder.find_references_in_document(doc)
        self.maxDiff = None
        self.assertMultiLineEqual('''<body xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <section id="section-1">
    <num>1.</num>
    <heading>Tester</heading>
    <paragraph id="section-1.paragraph-0">
      <content>
        <p>the <ref href="/za/act/1996/constitution">Constitution</ref></p>
        <p>the <ref href="/za/act/1996/constitution">Constitution, 1996</ref></p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of South Africa</ref></p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa</ref></p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa, 1996</ref></p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa 1996</ref></p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa Act, 1996</ref></p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa, 1996</ref> ( <ref href="/za/act/1996/constitution">Act 108 of 1996</ref> )</p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa, 1996</ref> ( <ref href="/za/act/1996/constitution">Act No 108 of 1996</ref> )</p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa, 1996</ref> ( <ref href="/za/act/1996/constitution">Act No. 108 of 1996</ref> )</p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa Act, 1996</ref> ( <ref href="/za/act/1996/constitution">Act No. 108 of 1996</ref> )</p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa</ref>  <ref href="/za/act/1996/constitution">Act 108 of 1996</ref></p>
        <p>the <ref href="/za/act/1996/constitution">Constitution of the Republic of South Africa</ref> (<ref href="/za/act/1996/constitution">Act 108 of 1996</ref>)</p>
        <p>the below shouldn't match</p>
        <p>Constitutionally unsound</p>
        <p>is unconstitutional</p>
        <p>their constitution is poor</p>
      </content>
    </paragraph>
  </section>
</body>
''', etree.tostring(doc.doc.body, pretty_print=True))


class RefsFinderAFRTestCase(APITestCase):
    def setUp(self):
        self.finder = RefsFinderAFR()

    def test_find_simple(self):
        doc = Document(content=document_fixture(xml=u"""
<section id="section-1">
  <num>1.</num>
  <heading>Tester</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>Something to do with Wet no 22 van 2012.</p>
      <p>And another thing about Wet 4 van 1998.</p>
    </content>
  </paragraph>
</section>
        """))

        self.finder.find_references_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <section id="section-1">
    <num>1.</num>
    <heading>Tester</heading>
    <paragraph id="section-1.paragraph-0">
      <content>
        <p>Something to do with <ref href="/za/act/2012/22">Wet no 22 van 2012</ref>.</p>
        <p>And another thing about <ref href="/za/act/1998/4">Wet 4 van 1998</ref>.</p>
      </content>
    </paragraph>
  </section>
</body>
''', etree.tostring(doc.doc.body, pretty_print=True))

    def test_find_multiple_in_tail(self):
        doc = Document(content=document_fixture(xml=u"""
<section id="section-1">
  <num>1.</num>
  <heading>Tester</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>Something Wet 4 van 2000 and "<term>City</term>" means the (Wet No. 117 van 1998) and also Wet 5 van 2020;</p>
    </content>
  </paragraph>
</section>
        """))

        self.finder.find_references_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <section id="section-1">
    <num>1.</num>
    <heading>Tester</heading>
    <paragraph id="section-1.paragraph-0">
      <content>
        <p>Something <ref href="/za/act/2000/4">Wet 4 van 2000</ref> and "<term>City</term>" means the (<ref href="/za/act/1998/117">Wet No. 117 van 1998</ref>) and also <ref href="/za/act/2020/5">Wet 5 van 2020</ref>;</p>
      </content>
    </paragraph>
  </section>
</body>
''', etree.tostring(doc.doc.body, pretty_print=True))

    def test_ignore_existing(self):
        doc = Document(content=document_fixture(xml=u"""
<section id="section-1">
  <num>1.</num>
  <heading>Tester</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>Something to do with <ref href="/za/act/2012/22">Wet no 22 van 2012</ref>.</p>
      <p>And another thing about <ref href="/za/act/1998/4"><b>Wet 4 van 1998</b></ref>.</p>
    </content>
  </paragraph>
</section>
        """))

        self.finder.find_references_in_document(doc)
        self.assertMultiLineEqual('''<body xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <section id="section-1">
    <num>1.</num>
    <heading>Tester</heading>
    <paragraph id="section-1.paragraph-0">
      <content>
        <p>Something to do with <ref href="/za/act/2012/22">Wet no 22 van 2012</ref>.</p>
        <p>And another thing about <ref href="/za/act/1998/4"><b>Wet 4 van 1998</b></ref>.</p>
      </content>
    </paragraph>
  </section>
</body>
''', etree.tostring(doc.doc.body, pretty_print=True))

    def test_constitution(self):
        doc = Document(content=document_fixture(xml=u"""
<section id="section-1">
  <num>1.</num>
  <heading>Tester</heading>
  <paragraph id="section-1.paragraph-0">
    <content>
      <p>die Grondwet</p>
      <p>die Grondwet, 1996</p>
      <p>die Grondwet van Suid Afrika</p>
      <p>die Grondwet van die Republiek van Suid-Afrika</p>
      <p>die Grondwet van die Republiek van Suid-Afrika, 1996</p>
      <p>die Grondwet van die Republiek van Suid-Afrika 1996</p>
      <p>die Grondwet van die Republiek van Suid-Afrika Wet, 1996</p>
      <p>die Grondwet van die Republiek van Suid-Afrika, 1996 ( Wet 108 van 1996 )</p>
      <p>die Grondwet van die Republiek van Suid-Afrika, 1996 ( Wet No 108 van 1996 )</p>
      <p>die Grondwet van die Republiek van Suid-Afrika, 1996 ( Wet No. 108 van 1996 )</p>
      <p>die Grondwet van die Republiek van Suid-Afrika Wet, 1996 ( Wet No. 108 van 1996 )</p>
      <p>die Grondwet van die Republiek van Suid-Afrika  Wet 108 van 1996</p>
      <p>die Grondwet van die Republiek van Suid-Afrika (Wet 108 van 1996)</p>
      <p>the below shouldn't match</p>
      <p>enige grondwet</p>
    </content>
  </paragraph>
</section>
        """))

        self.finder.find_references_in_document(doc)
        self.maxDiff = None
        self.assertMultiLineEqual('''<body xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <section id="section-1">
    <num>1.</num>
    <heading>Tester</heading>
    <paragraph id="section-1.paragraph-0">
      <content>
        <p>die <ref href="/za/act/1996/constitution">Grondwet</ref></p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet, 1996</ref></p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van Suid Afrika</ref></p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika</ref></p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika, 1996</ref></p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika 1996</ref></p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika Wet, 1996</ref></p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika, 1996</ref> ( <ref href="/za/act/1996/constitution">Wet 108 van 1996</ref> )</p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika, 1996</ref> ( <ref href="/za/act/1996/constitution">Wet No 108 van 1996</ref> )</p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika, 1996</ref> ( <ref href="/za/act/1996/constitution">Wet No. 108 van 1996</ref> )</p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika Wet, 1996</ref> ( <ref href="/za/act/1996/constitution">Wet No. 108 van 1996</ref> )</p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika</ref>  <ref href="/za/act/1996/constitution">Wet 108 van 1996</ref></p>
        <p>die <ref href="/za/act/1996/constitution">Grondwet van die Republiek van Suid-Afrika</ref> (<ref href="/za/act/1996/constitution">Wet 108 van 1996</ref>)</p>
        <p>the below shouldn't match</p>
        <p>enige grondwet</p>
      </content>
    </paragraph>
  </section>
</body>
''', etree.tostring(doc.doc.body, pretty_print=True))
