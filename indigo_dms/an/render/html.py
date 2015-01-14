import os
import lxml.etree as ET 

class HTMLRenderer(object):
    def __init__(self, xslt_filename=None):
        if not xslt_filename:
            xslt_filename = os.path.join(os.path.dirname(__file__), 'xsl/act.xsl')
        self.xslt = ET.XSLT(ET.parse(xslt_filename))

    def render(self, node):
        """ Render an XML Tree or Element object into an HTML string """
        return ET.tostring(self.xslt(node))
    
    def render_xml(self, xml):
        """ Render an XML string into an HTML string """
        return self.render(ET.fromstring(xml.encode('utf-8')))
