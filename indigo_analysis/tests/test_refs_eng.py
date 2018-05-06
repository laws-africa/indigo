# -*- coding: utf-8 -*-

from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from lxml import etree

from indigo_api.tests.fixtures import *  # noqa
from indigo_analysis.refs.eng import RefsFinderENG
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
