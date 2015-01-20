from lxml import objectify 
from lxml import etree

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

    def __init__(self, xml):
        """ Setup a new instance with the string in `xml`. """
        self.root = objectify.fromstring(xml).getroot()
        self.meta = root.act.meta
        self.body = root.act.body

    @property
    def short_title(self):
        return self.meta.identification.FRBRWork.FRBRalias.get('value')

    @short_title.setter
    def short_title(self, value):
        self.meta.identification.FRBRWork.FRBRalias.set('value', value)

    def to_xml(self):
        return etree.tostring(self.root, pretty_print=True)

