import os
import lxml.etree as ET


class HTMLRenderer(object):
    """
    Renders an Akoma Ntoso Act XML document into HTML using XLS transforms.

    For the most part, the document tree is copied directly by converting
    Akoma Ntoso elements into **div** or **span** HTML elements. The class
    attribute on each element is set to ``an-element`` where `element` is the
    Akoma Ntoso element name.  The **id** attribute is copied over directly.
    """

    def __init__(self, act=None, uri=None, country=None, language=None, subtype=None, xslt_filename=None, xslt_dir=None):
        """
        Create a new, re-usable render. The renderer must be able to find an appropriate
        XSL stylesheet based on the provided parameters.

        :param act: the act from which to take the language, country, etc.
        :param `cobalt.uri.FrbrUri` uri: the URI from which to take language, country, etc.
        :param country: two-letter country code
        :param language: three- or two-letter language code
        :param subtype: document subtype (eg. 'bylaw'), or None
        :param xslt_dir: directory in which to look for files
        :param xslt_filename: specify filename directly, all other params ignored
        """
        if xslt_filename is None:
            xslt_filename = self.find_xslt(act, uri, country, language, xslt_dir)

        if not xslt_filename:
            xslt_filename = os.path.join(os.path.dirname(__file__), 'xsl/act.xsl')
        self.xslt = ET.XSLT(ET.parse(xslt_filename))

    def render(self, node):
        """ Render an XML Tree or Element object into an HTML string """
        return ET.tostring(self.xslt(node))

    def render_xml(self, xml):
        """ Render an XML string into an HTML string """
        if not isinstance(xml, str):
            xml = xml.encode('utf-8')
        return self.render(ET.fromstring(xml))

    def find_xslt(self, act=None, uri=None, country=None, language=None, subtype=None, xslt_dir=None):
        xslt_dir = xslt_dir or os.path.join(os.path.dirname(__file__), 'xsl')

        if act:
            uri = uri or act.frbr_uri

        if uri:
            language = language or uri.language
            country = country or uri.country
            subtype = subtype or uri.subtype

        language = language or "eng"
        country = country or "za"

        options = []
        if subtype:
            options.append('_'.join(["act", subtype, language, country]))
            options.append('_'.join(["act", subtype, language]))
            options.append('_'.join(["act", subtype, country]))
            options.append('_'.join(["act", subtype]))

        options.append('_'.join(["act", language, country]))
        options.append('_'.join(["act", language]))
        options.append('_'.join(["act", country]))
        options.append('act')

        options = [os.path.join(xslt_dir, f + ".xsl") for f in options]

        for fname in options:
            if os.path.isfile(fname):
                return fname

        raise ValueError("Couldn't find XSLT file, not even the default, in %s" % xslt_dir)
