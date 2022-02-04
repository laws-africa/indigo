import re
import logging
import shutil
import tempfile
from zipfile import BadZipFile
import math

from lxml import html, etree
from lxml.html.clean import Cleaner
import cssutils
import mammoth

from indigo.xmlutils import unwrap_element, merge_adjacent
from indigo_api.utils import filename_candidates, find_best_static
from .pipeline import Stage, ImportAttachment, Pipeline

log = logging.getLogger(__name__)


class DocxToHtml(Stage):
    """ Converts a DOCX file into HTML.

    Reads: context.source_file
    Writes: context.html_text, context.attachments
    """
    def __call__(self, context):
        helper = {'counter': 0}

        def stash_image(image):
            """ Helper that handles an image found in the DOCX file. It stores a corresponding
            attachment on the import context, and gives the file a unique name that is used to
            refer to the image in the HTML.
            """
            helper['counter'] += 1
            try:
                with image.open() as img:
                    # copy the file to somewhere temporary
                    f = tempfile.NamedTemporaryFile()
                    shutil.copyfileobj(img, f)
                    f.seek(0)

                    file_ext = image.content_type.split('/')[1]
                    filename = f'img{helper["counter"]}.{file_ext}'
                    context.attachments.append(ImportAttachment(
                        filename=filename,
                        content_type=image.content_type,
                        file=f,
                    ))
                return {'src': 'media/' + filename}
            except KeyError as e:
                # raised when the image can't be found in the zip file
                log.info(f"Image cannot be found in docx file; ignoring", exc_info=e)
                return {}

        try:
            result = mammoth.convert_to_html(context.source_file, convert_image=mammoth.images.img_element(stash_image))
            html = result.value
        except BadZipFile:
            raise ValueError("This doesn't seem to be a valid DOCX file.")

        context.html_text = html


class ParseHtml(Stage):
    """ Parse html with lxml.html.

    Reads: context.html_text
    Writes: context.html
    """
    def __call__(self, context):
        context.html = html.fromstring(context.html_text)


class CleanHtml(Stage):
    """ Clean dangerous HTML.

    Reads: context.html
    Writes: context.html
    """
    cleaner = Cleaner(
        style=True,
        inline_style=False,
        safe_attrs=list(Cleaner.safe_attrs) + ['style']
    )

    def __call__(self, context):
        context.html = self.cleaner.clean_html(context.html)


class SimplifyHtml(Stage):
    """ Simplify HTML:

    * strong to b
    * em to i
    * remove unused headers, styles, scripts etc.
    """

    xsl = """
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html" encoding="utf-8" />
  <xsl:strip-space elements="p"/>

  <!-- ignore these elements -->
  <xsl:template match="head|style|script|link" />

  <!-- unwrap these elements -->
  <xsl:template match="div[not(starts-with(@id, 'sdfootnote'))] | span | font">
    <xsl:apply-templates />
  </xsl:template>

  <!-- strong to b -->
  <xsl:template match="strong">
    <b><xsl:apply-templates /></b>
  </xsl:template>

  <!-- em to i -->
  <xsl:template match="em">
    <i><xsl:apply-templates /></i>
  </xsl:template>

  <!-- for most nodes, just copy -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
"""

    def __call__(self, context):
        xslt = etree.XSLT(etree.fromstring(self.xsl))
        context.html = html.fromstring(str(xslt(context.html)))


class NormaliseHtmlTextWhitespace(Stage):
    """ Strip and normalise whitespace in HTML text.

    Reads: context.html_text
    Writes: context.html_text
    """
    def __call__(self, context):
        # &nbsp; to space
        context.html_text = context.html_text.replace('&nbsp;', ' ')

        # tabs to spaces, multiple spaces and newlines to one
        context.html_text = re.sub(r'[\r\n\s]+', ' ', context.html_text)


class MergeAdjacentInlines(Stage):
    """ Merge adjacent b (and i) tags that are directly adjacent.

    eg::

        <b>text</b><b>more</b>

    becomes::

        <b>textmore</b>

    Reads: context.html
    Writes: context.html
    """
    def __call__(self, context):
        for e in context.html.xpath('//b | //i'):
            nxt = e.getnext()
            while nxt is not None and nxt.tag == e.tag and not e.tail:
                merge_adjacent(e, nxt)
                nxt = e.getnext()


class RemoveEmptyInlines(Stage):
    """ Remove inline elements that are empty (no children, no text or just whitespace).

    Reads: context.html
    Writes: context.html
    """
    def __call__(self, context):
        nodes = 'a b i sup sub'.split()
        xpath = ' | '.join(f'//{n}' for n in nodes)
        for node in context.html.xpath(xpath):
            # node has no children, and either no text or just whitespace
            # in the case of whitespace, it is preserved
            if not list(node) and (not node.text or not node.text.strip()):
                unwrap_element(node)


class MergeUl(Stage):
    """ Merge consecutive UL lists together

    Reads: context.html
    Writes: context.html
    """
    def __call__(self, context):
        for ul in context.html.xpath('//ul'):
            prev = ul.getprevious()
            if prev is not None and prev.tag == 'ul':
                # merge this ul into the previous one
                for kid in ul:
                    prev.append(kid)
                ul.getparent().remove(ul)


class CleanTables(Stage):
    """ Clean tables in the html as follows:

    - strip any width attributes on the table
    - normalize existing width attributes on table cells from absolutes into percentages
    - remove any padding styles on table cells
    - remove cell border styles that set a border to none

    Reads: context.html
    Writes: context.html
    """
    def __call__(self, context):
        for table in context.html.xpath('//table'):
            # strip table width
            if table.attrib.get('width'):
                table.attrib.pop('width')

            if table.attrib.get('cellpadding'):
                table.attrib.pop('cellpadding')

            if table.attrib.get('cellspacing'):
                table.attrib.pop('cellspacing')

            for row in table.xpath('.//tr'):
                total_row_width = sum([int(c.attrib['width'].replace('%', '')) for c in row if c.attrib.get('width')])
                for cell in row:
                    style = cssutils.parseStyle(cell.attrib.get('style'))

                    # normalize cell width to % based on total row width
                    width = cell.attrib.get('width')
                    if width:
                        width = int(width.replace('%', ''))
                        w_pct = math.floor(width / total_row_width * 100)
                        style['width'] = f'{w_pct}%'
                        cell.attrib['style'] = style.cssText.replace('\n', ' ')
                        cell.attrib.pop('width')

                    if style and cell.attrib.get('style'):
                        # remove any padding
                        style.removeProperty('padding')
                        style.removeProperty('padding-top')
                        style.removeProperty('padding-bottom')
                        style.removeProperty('padding-left')
                        style.removeProperty('padding-right')

                        # remove cell border styles that set any border to none
                        if style.getPropertyValue('border') == 'none':
                            style.removeProperty('border')

                        if style.getPropertyValue('border-top') == 'none':
                            style.removeProperty('border-top')

                        if style.getPropertyValue('border-bottom') == 'none':
                            style.removeProperty('border-bottom')

                        if style.getPropertyValue('border-left') == 'none':
                            style.removeProperty('border-left')

                        if style.getPropertyValue('border-right') == 'none':
                            style.removeProperty('border-right')

                        if style.getCssText():
                            cell.attrib['style'] = style.cssText.replace('\n', ' ')
                        else:
                            cell.attrib.pop('style')

                    if cell.attrib.get('height'):
                        cell.attrib.pop('height')


class StripParaWhitespace(Stage):
    """ Strip whitespace at the start of p tags.

    Reads: context.html
    Writes: context.html
    """
    whitespace = '  '

    def __call__(self, context):
        for p in context.html.xpath('//p'):
            if p.text:
                p.text = p.text.lstrip(self.whitespace)


class HtmlToSlawText(Stage):
    """ Transform HTML into Slaw-friendly text.

    Reads: context.html
    Writes: context.text
    """
    html_to_text_xsl_prefix = 'xsl/html_to_akn_text_'

    def __call__(self, context):
        candidates = filename_candidates(context.doc, prefix=self.html_to_text_xsl_prefix, suffix='.xsl')
        xslt_filename = find_best_static(candidates)
        if not xslt_filename:
            raise ValueError(f"Couldn't find XSLT file to use for {context.doc}, tried: {candidates}")

        xslt = etree.XSLT(etree.parse(xslt_filename))
        context.text = str(xslt(context.html))


parse_and_clean = Pipeline([
    NormaliseHtmlTextWhitespace(),
    ParseHtml(),
    CleanHtml(),
    SimplifyHtml(),
    MergeAdjacentInlines(),
    RemoveEmptyInlines(),
    MergeUl(),
    CleanTables(),
    StripParaWhitespace(),
])
