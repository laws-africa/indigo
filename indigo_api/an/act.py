import re

from lxml import objectify 
from lxml import etree

encoding_re = re.compile('encoding="[\w-]+"')

class Act(object):
    """
    An Act wraps a single {http://www.akomantoso.org/ AkomaNtoso 2.0 XML} act document in the form of a
    XML Element object.

    The Act object provides quick access to certain sections of the document.

    Properties:

        `root`: lxml.objectify.ObjectifiedElement root of the XML document
        `meta`: lxml.objectify.ObjectifiedElement meta element
        `meta`: lxml.objectify.ObjectifiedElement body element
    """

    def __init__(self, xml=None):
        """ Setup a new instance with the string in `xml`. """
        if not xml:
            # use an empty document
            xml = EMPTY_DOCUMENT

        encoding = encoding_re.search(xml, 0, 200)
        if encoding:
            # lxml doesn't like unicode strings with an encoding element, so
            # change to bytes
            xml = xml.encode('utf-8')

        self.root = objectify.fromstring(xml)
        self.meta = self.root.act.meta
        self.body = self.root.act.body

    @property
    def title(self):
        return self.meta.identification.FRBRWork.FRBRalias.get('value')

    @title.setter
    def title(self, value):
        self.meta.identification.FRBRWork.FRBRalias.set('value', value)

    def to_xml(self):
        return etree.tostring(self.root, pretty_print=True)

    @property
    def body_xml(self):
        return etree.tostring(self.body, pretty_print=True)

    @body_xml.setter
    def body_xml(self, xml):
        """ Insert the string `xml` as the body of the document. The XML must be 
        rooted at a `body` element. """
        new_body = objectify.fromstring(xml)
        new_body.tag = 'body'
        self.body.getparent().replace(self.body, new_body)
        self.body = new_body


EMPTY_DOCUMENT = """<?xml version="1.0"?>
<akomaNtoso xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.akomantoso.org/2.0" xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd">
  <act contains="originalVersion">
    <meta>
      <identification source="">
        <FRBRWork>
          <FRBRthis value="/za/act/1900/1/main"/>
          <FRBRuri value="/za/act/1900/1/"/>
          <FRBRalias value="Untitled"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/za/act/1900/1/main/eng@"/>
          <FRBRuri value="/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/za/act/1900/1/main/eng@"/>
          <FRBRuri value="/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
        </FRBRManifestation>
      </identification>
    </meta>
    <body>
      <section id="section-1">
        <content>
          <p></p>
        </content>
      </section>
    </body>
  </act>
</akomaNtoso>
"""
