import os.path
import re
from copy import deepcopy

from lxml import etree
import cssutils

from cobalt.akn import AKN_NAMESPACES, DEFAULT_VERSION, get_maker
from bluebell.akn import ParseError
from bluebell.parser import parse_to_xml_bytes
from docpipe.html import ParseHtml
from docpipe.pipeline import Stage
from docpipe.xmlutils import unwrap_element
from indigo.xmlutils import default_bluebell_source, parse_html_str


def chomp_left(elem, count):
    """ Remove count chars of text from the left of elem and its contents.
    """
    for text in elem.xpath('.//text()'):
        # chomp as much as we can, up to the length of text
        chomped = min(len(text), count)
        count = count - chomped

        parent = text.getparent()
        if text.is_tail:
            parent.tail = parent.tail[chomped:]
        else:
            parent.text = parent.text[chomped:]

        if not count:
            return


def is_centered(elem):
    """ Try to guess if the elem is centered.
    """
    return elem.attrib.get("align") == "center"


class RemoveInlines(Stage):
    """ Remove certain inlines.

    Reads: context.html
    Writes: context.html
    """

    inlines = ["b", "i"]

    def __call__(self, context):
        xpath = "|".join(f".//{x}" for x in self.inlines)
        for elem in context.html.xpath(xpath):
            unwrap_element(elem)


class ParseBluebellText(Stage):
    """ Parse bluebell text into an XML object tree (not text).

    Reads: context.text
    Writes: context.xml
    """
    def __call__(self, context):
        frbr_uri = context.frbr_uri.clone()
        frbr_uri.work_component = 'main'
        root = context.fragment or frbr_uri.doctype

        try:
            xml_bytes = parse_to_xml_bytes(
                context.text,
                root,
                frbr_uri,
                eid_prefix=context.fragment_id_prefix or '',
                source=default_bluebell_source(),
            )
        except ParseError as e:
            raise ValueError(e)

        if context.fragment:
            # fragment must be wrapped in AKN tags
            # TODO: use a partial document from Cobalt?
            ns = AKN_NAMESPACES[DEFAULT_VERSION]
            xml = xml_bytes.decode('utf-8')
            xml = f'<akomaNtoso xmlns="{ns}">{xml}</akomaNtoso>'
            xml_bytes = xml.encode('utf-8')

        # turn into XML tree
        context.xml = etree.fromstring(xml_bytes)


class WrapAnnotations(Stage):
    """ Wrap the content of <p>s that start with [ and end with ] (and have no ]s before the end)
        in <remark status="editorial">s.

    Reads: context.xml
    Writes: context.xml
    """

    ns = AKN_NAMESPACES[DEFAULT_VERSION]
    annotation_re = re.compile(r'^\[[^]]+\]$')

    def __call__(self, context):
        maker = get_maker()
        for annotation_elem in context.xml.xpath(
                './/a:*['
                '(self::a:p or self::a:listIntroduction or self::a:listWrapUp)'
                ' and starts-with(., "[")]',
                namespaces={'a': self.ns}):
            text = ''.join(annotation_elem.itertext())
            match = re.match(self.annotation_re, text)
            if match:
                remark = maker('remark', status='editorial')
                # move the text from the element into the new remark
                remark.text = annotation_elem.text
                annotation_elem.text = None
                # get any children as well (e.g. <sup>)
                for c in annotation_elem:
                    remark.append(c)
                assert not list(annotation_elem.getchildren())

                # make the remark the direct child of the element
                annotation_elem.append(remark)


class HtmlToBluebellText(Stage):
    """ Convert HTML into bluebell text using XSL.

    Reads: context.html
    Writes: context.text
    """
    xsl_fname = os.path.join(os.path.dirname(__file__), 'xsl/html-to-bluebell-text.xsl')

    def __call__(self, context):
        xslt = etree.XSLT(etree.parse(self.xsl_fname))
        # do a deepcopy, otherwise the XSLT seems to modify the context.html
        context.text = str(xslt(deepcopy(context.html)))


class SimplifyHtml(Stage):
    """ Basic HTML simplification using XSL. strong to b, em to i, drop some tags.
    Reads: context.html
    Writes: context.html
    """
    xsl_fname = os.path.join(os.path.dirname(__file__), 'xsl/html-clean.xsl')

    def __call__(self, context):
        xslt = etree.XSLT(etree.parse(self.xsl_fname))
        # When context.html is a root div element, the xslt ignores the div and produces a bunch of standalone p tags.
        # So, turn into text and re-parse, and then ensure there's a single container root
        context.html = parse_html_str(str(xslt(context.html)))
        ParseHtml().ensure_container_root(context)


class CleanTableStyles(Stage):
    """ Additional table cleaning.

    - remove table border styles

    Reads: context.html
    Writes: context.html
    """

    def __call__(self, context):
        for cell in context.html.xpath('.//td[@style] | .//th[@style]'):
            style = cssutils.parseStyle(cell.attrib.get('style'))

            # remove cell border styles that set any border to none
            for prop in style.keys():
                if prop.startswith('border'):
                    style.removeProperty(prop)

            if style.getCssText():
                cell.attrib['style'] = style.cssText.replace('\n', ' ')
            else:
                cell.attrib.pop('style')
