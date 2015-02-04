import re
from datetime import date

from lxml import objectify 
from lxml import etree
import arrow

encoding_re = re.compile('encoding="[\w-]+"')

DATE_FORMAT = "%Y-%m-%d"

def datestring(value):
    if value is None:
        return ""
    elif isinstance(value, basestring):
        return value
    else:
        return value.strftime(DATE_FORMAT)


class Act(object):
    """
    An Act wraps a single {http://www.akomantoso.org/ AkomaNtoso 2.0 XML} act document in the form of a
    XML Element object.

    The Act object provides quick access to certain sections of the document.

    Properties:

        `root`: lxml.objectify.ObjectifiedElement root of the XML document
        `meta`: lxml.objectify.ObjectifiedElement meta element
        `body`: lxml.objectify.ObjectifiedElement body element
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

        self.namespace = self.root.nsmap[None]
        self._maker = objectify.ElementMaker(annotate=False, namespace=self.namespace, nsmap=self.root.nsmap)


    @property
    def title(self):
        return self.meta.identification.FRBRWork.FRBRalias.get('value')

    @title.setter
    def title(self, value):
        self.meta.identification.FRBRWork.FRBRalias.set('value', value)

    @property
    def work_date(self):
        return arrow.get(self.meta.identification.FRBRWork.FRBRdate.get('date')).date()

    @work_date.setter
    def work_date(self, value):
        self.meta.identification.FRBRWork.FRBRdate.set('date', datestring(value))


    @property
    def expression_date(self):
        return arrow.get(self.meta.identification.FRBRExpression.FRBRdate.get('date')).date()

    @expression_date.setter
    def expression_date(self, value):
        self.meta.identification.FRBRExpression.FRBRdate.set('date', datestring(value))


    @property
    def manifestation_date(self):
        return arrow.get(self.meta.identification.FRBRManifestation.FRBRdate.get('date')).date()

    @manifestation_date.setter
    def manifestation_date(self, value):
        self.meta.identification.FRBRManifestation.FRBRdate.set('date', datestring(value))


    @property
    def publication_name(self):
        pub = self._get('meta.publication')
        return pub.get('name') if pub is not None else None

    @publication_name.setter
    def publication_name(self, value):
        pub = self._ensure('meta.publication', after=self.meta.identification)
        pub.set('name', value)
        pub.set('showAs', value)


    @property
    def publication_date(self):
        pub = self._get('meta.publication')
        return pub.get('date') if pub is not None else None

    @publication_date.setter
    def publication_date(self, value):
        self._ensure('meta.publication', after=self.meta.identification)\
                .set('date', datestring(value))


    @property
    def publication_number(self):
        pub = self._get('meta.publication')
        return pub.get('number') if pub is not None else None

    @publication_number.setter
    def publication_number(self, value):
        self._ensure('meta.publication', after=self.meta.identification)\
                .set('number', value)


    @manifestation_date.setter
    def manifestation_date(self, value):
        self.meta.identification.FRBRManifestation.FRBRdate.set('date', datestring(value))

    @property
    def frbr_uri(self):
        return self.meta.identification.FRBRWork.FRBRuri.get('value')

    @frbr_uri.setter
    def frbr_uri(self, value):
        if not value.endswith('/'):
            value = value + "/"

        self.meta.identification.FRBRWork.FRBRuri.set('value', value)

        language = self.meta.identification.FRBRExpression.FRBRlanguage.get('language', 'eng')
        lang_uri = value + language + "@"
        self.meta.identification.FRBRExpression.FRBRuri.set('value', lang_uri)
        self.meta.identification.FRBRManifestation.FRBRuri.set('value', lang_uri)

    @property
    def number(self):
        """ The act number, derived from :data:`frbr_uri`. Read-only. """
        if self.frbr_uri:
            try:
                return self.frbr_uri.split('/')[4]
            except IndexError:
                pass

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


    def _ensure(self, name, after):
        """ Hack help to get an element if it exists, or create it if it doesn't.
        *name* is a dotted path from *self*, *after* is where to place the new
        element if it doesn't exist. """
        node = self._get(name)
        if node is None:
            # TODO: what if nodes in the path don't exist?
            node = self._make(name.split('.')[-1])
            after.addnext(node)

        return node

    def _make(self, elem):
        return getattr(self._maker, elem)()


    def _get(self, name):
        parts = name.split('.')
        node = getattr(self, parts[0])
        for p in parts[1:]:
            try:
                node = getattr(node, p)
            except AttributeError:
                return None
        return node


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
