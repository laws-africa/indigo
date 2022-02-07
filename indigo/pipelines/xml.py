from lxml import etree

from .pipeline import Stage


class SerialiseXml(Stage):
    """ Serialises XML into a unicode string in xml_text.

    Reads: context.xml
    Writes: context.xml_text
    """
    def __call__(self, context):
        context.xml_text = etree.tostring(context.xml, encoding='unicode')
