import datetime
import logging
import math
import os
import re
import shutil
import tempfile
from collections import defaultdict
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse, urlunparse

from django.conf import settings
from django.contrib.staticfiles.finders import find as find_static
from django.template.loader import render_to_string, get_template
from django.utils.translation import override, gettext_lazy as _
from ebooklib import epub
from languages_plus.models import Language
from lxml import etree
from lxml import etree as ET
from sass_processor.processor import SassProcessor

from indigo.analysis.toc.base import descend_toc_pre_order
from indigo.plugins import plugins, LocaleBasedMatcher
from indigo.xmlutils import parse_html_str
from indigo_api.models import Colophon
from indigo_api.pdf import run_fop
from indigo_api.utils import filename_candidates, find_best_template, find_best_static

log = logging.getLogger(__name__)


class HTMLExporter:
    """ Export (render) AKN documents as as HTML.
    """
    def __init__(self, coverpage=True, standalone=False, template_name=None, resolver=None, media_resolver_use_akn_prefix=False):
        self.template_name = template_name
        self.standalone = standalone
        self.coverpage = coverpage
        self.resolver = resolver or settings.RESOLVER_URL
        self.media_url = ''
        self.media_resolver_use_akn_prefix = media_resolver_use_akn_prefix

    def render(self, document, element=None):
        """ Render this document to HTML.

        :param document: document to render if +element+ is None
        :param element: element to render (optional)
        """
        self.document = document

        # use this to render the bulk of the document
        renderer = self._xml_renderer(document)

        if element is not None:
            # just a fragment of the document
            content_html = renderer.render(element)
            if not self.standalone:
                # we're done
                return content_html
        else:
            # the entire document
            if document.document_xml:
                content_html = renderer.render_xml(document.document_xml)
            else:
                content_html = ''

        # find the template to use
        template_name = self.template_name or self.find_template(document)

        context = self.get_context_data(**{
            'document': document,
            'element': element,
            'content_html': content_html,
            'renderer': renderer,
            'coverpage': self.coverpage,
            'coverpage_template': self.coverpage_template(document),
        })

        # Now render some boilerplate around it.
        if self.standalone:
            context['template_name'] = template_name
            context['colophon'] = self.find_colophon(document)
            return render_to_string('indigo_api/akn/export/standalone.html', context)
        else:
            return render_to_string(template_name, context)

    def coverpage_template(self, document):
        return self.find_template(document, prefix='coverpage_')

    def render_coverpage(self, document):
        template_name = self.coverpage_template(document)
        return render_to_string(template_name, self.get_context_data(document=document))

    def get_context_data(self, **kwargs):
        """ Get the context data passed to the HTML template.
        """
        context = {
            'resolver_url': self.resolver,
            'media_resolver_use_akn_prefix': self.media_resolver_use_akn_prefix,
        }
        context.update(kwargs)
        return context

    def find_colophon(self, document):
        return Colophon.objects.filter(country=document.work.country).first()

    def find_template(self, document, prefix='', suffix='.html'):
        """ Return the filename of a template to use to render this document.

        The normal Django templating system is used to find a template. The first template
        found is used.
        """
        candidates = filename_candidates(document, prefix='indigo_api/akn/' + prefix, suffix=suffix)
        best = find_best_template(candidates)
        if not best:
            raise ValueError("Couldn't find an HTML template to use for %s, tried: %s" % (document, candidates))
        return best

    def find_xslt(self, document):
        """ Return the filename of an xslt template to use to render this document.

        The normal Django templating system is used to find a template. The first template
        found is used.
        """
        candidates = filename_candidates(document, prefix='xsl/html_', suffix='.xsl')
        best = find_best_static(candidates)
        if not best:
            raise ValueError("Couldn't find XSLT file to use for %s, tried: %s" % (document, candidates))
        return best

    def _xml_renderer(self, document):
        params = {
            'resolverUrl': self.resolver,
            'mediaUrl': self.media_url or '',
            'lang': document.language.code,
            'documentType': document.nature,
            'subtype': document.subtype or '',
            'country': document.work.country.code,
            'locality': (document.work.locality.code if document.work.locality else ''),
        }

        return XSLTRenderer(xslt_params=params, xslt_filename=self.find_xslt(document))


@plugins.register('pdf-exporter')
class PDFExporter(HTMLExporter, LocaleBasedMatcher):
    """ Exports (renders) AKN documents as PDFs using FOP.
    """
    locale = (None, None, None)
    resolver_url = settings.RESOLVER_URL

    # list of countries that shouldn't be included in the coverpage
    dont_include_countries = []
    base_xsl_fo_dir = os.path.join(os.path.dirname(__file__), 'static', 'xsl', 'fo')
    inline_glyphs = ['☐']

    def render(self, document, element=None):
        # we don't support rendering partial PDFs
        if element:
            raise NotImplementedError
        log.info(f'Rendering PDF for document {document.pk} ({document.frbr_uri})')
        self.insert_coverpage(document)
        self.insert_static_content(document)
        self.insert_frontmatter(document)

        with tempfile.TemporaryDirectory() as tmpdir:
            # copy over assets required by our templates, like logos and coats of arms
            # stash_assets updates the paths to static images in document.doc.main
            self.stash_assets(document, tmpdir)

            # copy images on each document
            self.stash_images(document, tmpdir)

            # use the resolver for the appropriate external links (done for coverpage separately)
            self.adjust_refs(document.doc)
            # make eIds in the XML unique; else FOP complains
            self.make_eids_unique(document.doc)
            # fix tables to have the right number of columns and rows; else FOP complains
            self.resize_tables(document.doc)
            # write the XML to file
            xml = etree.tostring(document.doc.main, encoding='unicode')
            # any final adjustments to the XML string
            xml = self.final_tweaks(xml)
            xml_file = os.path.join(tmpdir, 'raw.xml')
            with open(xml_file, "wb") as f:
                f.write(xml.encode('utf-8'))

            xsl_fo = self.find_xsl_fo(document)
            self.update_base_xsl_fo_dir(xsl_fo)
            outf_name = os.path.join(tmpdir, "out.pdf")
            run_fop(outf_name, tmpdir, xml_file, xsl_fo)
            return open(outf_name, 'rb').read()

    def insert_coverpage(self, document):
        """ Generates the coverpage and inserts it before the body in the XML.
            The document's document_xml isn't updated.
        """
        coverpage = self.render_coverpage(document)
        coverpage_xml = self.html_to_xml(coverpage)
        # insert the coverpage before the main content (preface / preamble / body)
        document.doc.meta.addnext(coverpage_xml)

    def html_to_xml(self, html_string):
        """ Convert an HTML string into an XML string.
        """
        xslt = etree.XSLT(etree.parse(find_static('xsl/html_to_xml.xsl')))
        # apply xslt
        xml = str(xslt(parse_html_str(html_string)))
        # turn string into bytes and parse into xml
        return etree.fromstring(xml.encode('utf-8'))

    def insert_static_content(self, document):
        """ Generates the static content used in running headers and footers and inserts it before the body
            (and before the coverpage and frontmatter if present) in the XML.
            This allows us to use translation tags in the template rather than doing it in FO.
            The document's document_xml isn't updated.
        """
        # explicitly set the document's language for e.g. numbered title to be translated; deactivate after
        with override(document.django_language, deactivate=True):
            static_content = render_to_string(self.static_content_template(document), self.get_static_content_context(document))
        static_content_xml = etree.fromstring(static_content.encode('utf-8'))
        # insert the static content before the frontmatter, coverpage, or main content (preface / preamble / body)
        document.doc.meta.addnext(static_content_xml)

    def static_content_template(self, document):
        return self.find_template(document, prefix='export/pdf_static_content_', suffix='.xml')

    def get_static_content_context(self, document):
        return {
            'document': document,
            'ns': document.doc.namespace,
            'place_string': self.get_place_string(document),
            'notices': self.get_notices(document, short=True),
        }

    def get_place_string(self, document):
        """ Get the appropriate string based on the locality and country, in the right language.
        """
        locality = document.work.locality.name if document.work.locality else None
        country = document.work.country.name if document.country not in self.dont_include_countries else None
        if locality and country:
            return f'{_(locality)}, {_(country)}'
        elif locality:
            return _(locality)
        elif country:
            return _(country)

    def insert_frontmatter(self, document):
        """ Generates the frontmatter and inserts it before the body (and coverpage if present) in the XML.
            The document's document_xml isn't updated.
        """
        # explicitly set the document's language for e.g. numbered title to be translated; deactivate after
        with override(document.django_language, deactivate=True):
            frontmatter = render_to_string(self.frontmatter_template(document), self.get_frontmatter_context(document))
        frontmatter_xml = etree.fromstring(frontmatter.encode('utf-8'))
        # insert the frontmatter before the coverpage, or the main content (preface / preamble / body)
        document.doc.meta.addnext(frontmatter_xml)

    def frontmatter_template(self, document):
        return self.find_template(document, prefix='export/pdf_frontmatter_', suffix='.xml')

    def get_frontmatter_context(self, document):
        toc = self.get_base_toc(document)
        for e in descend_toc_pre_order(toc):
            if e.basic_unit or e.type in ['component', 'attachment']:
                e.children = []
        toc = [e.as_dict() for e in toc if e.type not in ['preface', 'preamble']]

        return {
            'document': document,
            'ns': document.doc.namespace,
            'toc': toc,
            'include_country': document.country not in self.dont_include_countries,
            'place_string': self.get_place_string(document),
            'notices': self.get_notices(document),
        }

    def get_notices(self, document, short=False):
        work = document.work
        notices = []

        if short:
            # we only care if it's uncommenced and/or repealed for the running header
            if not work.commenced and work.repealed_date:
                return _('Not commenced; Repealed')
            if not work.commenced:
                return _('Not commenced')
            if work.repealed_date:
                return _('Repealed')
            return

        # repeal
        if work.repealed_date:
            notice = _('This %(friendly_type)s was <b>repealed</b> on %(date)s by <ref href="%(url)s">%(work)s</ref>') % {
                'friendly_type': work.friendly_type(), 'date': work.repealed_date, 'work': work.repealed_by.title, 'url': work.repealed_by.frbr_uri}
            notice += f' ({work.repealed_by.numbered_title()}).' if work.repealed_by.numbered_title() else '.'
            notices.append(notice)

        # commencement
        if not work.commenced:
            notices.append(_('This %(friendly_type)s has <b>not yet come into force</b>.') % {'friendly_type': work.friendly_type()})
        # no notice for an unknown commencement date (commenced is True but there are no commencements)
        elif work.commencements.exists():
            latest_commencement_date = work.latest_commencement_date()
            if work.all_uncommenced_provision_ids(date=document.expression_date, return_bool=True):
                notices.append(_('This %(friendly_type)s has not yet come into force in full. '
                                 'See the commencements table for more information.') % {'friendly_type': work.friendly_type()})
            # no notice for a future commencement if the work also hasn't commenced in full
            elif latest_commencement_date and latest_commencement_date > datetime.date.today():
                notices.append(_('This %(friendly_type)s will come into force on %(date)s.') % {'friendly_type': work.friendly_type(), 'date': latest_commencement_date})

        # not the latest expression / amendments outstanding
        later_amendments = work.amendments_after_date(document.expression_date)
        if not document.is_latest_expression():
            notices.append(_('This is not the latest available version of this %(friendly_type)s. '
                             '<ref href="%(url)s">View it online</ref>.') % {'friendly_type': work.friendly_type(), 'url': work.frbr_uri})
        # no notice for outstanding amendments if this also isn't the latest expression
        elif later_amendments:
            numbered_titles = ', '.join(a.amending_work.numbered_title() or a.amending_work.short_title for a in later_amendments)
            notices.append(_('There are <b>outstanding amendments</b> that have not yet been applied:<br/>'
                             '%(numbered_titles)s.') % {'numbered_titles': numbered_titles})

        return notices

    def get_base_toc(self, document):
        return document.table_of_contents()

    def stash_assets(self, document, tmpdir):
        """ Stash assets that are either hard-coded into our templates, or provided by Django. These are stashed
        into 'assets', separately from document media which are stored in 'media'.

        Filenames relative to /static/ are preserved. For example:

        * /static/images/foo/bar.png -> assets/images/foo/bar.png
        """
        assets_dir = os.path.join(tmpdir, 'assets')
        os.makedirs(assets_dir)

        images = set()

        # static images
        # these are usually logos from the frontMatter or a coat of arms from the coverpage
        static_images = [img for img in
                         document.doc.main.xpath('//a:img[@src] | //img[@src]', namespaces={'a': document.doc.namespace})
                         if img.get('src').startswith('/static/')]
        for img in static_images:
            # strip /static/ from src and add to images
            src = img.get('src')[8:]
            images.add(src)
            # rewrite paths to be assets/foo/bar
            img.set('src', f'assets/{src}')

        # copy static images
        for fname in images:
            local_fname = find_static(fname)
            if not local_fname:
                # try removing the hash fingerprint for static assets, if present. Otherwise find_static can't find it.
                # images/coat-of-arms-na.6f5ffc9916ea.jpg -> images/coat-of-arms-na.jpg
                fname2 = re.sub(r'\.[a-f0-9]+(\.\w+)$', '\\1', fname)
                log.info(f"Static file for {fname} not found, trying {fname2}")
                local_fname = find_static(fname2)

            if local_fname:
                to_path = os.path.join(assets_dir, fname)
                log.info(f"Stashing {local_fname} to {to_path}")
                os.makedirs(os.path.dirname(to_path), exist_ok=True)
                shutil.copyfile(local_fname, to_path)
            else:
                log.warning(f"Static file for {fname} not found")

        # subclasses may want to add to the assets directory
        return assets_dir

    def stash_images(self, document, tmpdir):
        mediadir = os.path.join(tmpdir, 'media')
        os.makedirs(mediadir)

        for attachment in document.attachments.all():
            if attachment.mime_type.startswith('image/'):
                # copy file into media/<pk>/
                dest = os.path.join(mediadir, attachment.filename)
                log.info(f"Stashing image {attachment.filename} to {dest}")
                with open(dest, "wb") as f:
                    for chunk in attachment.file.chunks():
                        f.write(chunk)

    def escape_url(self, url):
        parsed_url = urlparse(url)
        return urlunparse((parsed_url.scheme, parsed_url.netloc, quote(unquote(parsed_url.path), safe='@"/'),
                           parsed_url.params, urlencode(parse_qsl(parsed_url.query)),
                           quote(unquote(parsed_url.fragment), safe=":"))).replace(" ", "%20")

    def adjust_refs(self, doc):
        """ Prefix absolute hrefs into fully-qualified URLs.
            Remove hrefs that will break FOP.
        """
        for ref in doc.root.xpath('//a:ref[@href]', namespaces={'a': doc.namespace}):
            href = ref.attrib['href']
            text = ''.join(ref.xpath('.//text()'))
            parsed_url = urlparse(href)

            if not parsed_url.scheme:
                # e.g. /akn/… which should be resolved, or
                # e.g. #sec_6 which should be left alone, or
                # e.g. example.com which should be removed
                if parsed_url.path and parsed_url.path.startswith('/'):
                    # /akn/… -- resolve it
                    parsed_resolver_url = urlparse(self.resolver_url)
                    new_path = parsed_resolver_url.path.rstrip('/') + parsed_url.path
                    ref.attrib['href'] = self.escape_url(urlunparse(
                        (parsed_resolver_url.scheme, parsed_resolver_url.netloc, new_path, parsed_url.params,
                         parsed_url.query, parsed_url.fragment)))
                elif not parsed_url.fragment:
                    # example.com -- remove it
                    log.info(f'Removing href "{href}" from text "{text}"')
                    del ref.attrib['href']
                # #sec_6 -- leave it alone

            elif not (parsed_url.netloc or parsed_url.path):
                # e.g. mailto: or https:// -- remove it
                log.info(f'Removing href "{href}" from the text "{text}"')
                del ref.attrib['href']

            else:
                # keep it as is but clean it up a bit
                ref.attrib['href'] = self.escape_url(urlunparse(parsed_url))

    def make_eids_unique(self, doc):
        """ Ensure there are no duplicate eIds.
        """
        all_eids = set()

        def ensure_unique(eid):
            if eid not in all_eids:
                return eid
            return ensure_unique(eid + '_x')

        for elem in doc.root.xpath('//a:*[@eId]', namespaces={'a': doc.namespace}):
            current = elem.attrib['eId']
            new = ensure_unique(current)
            all_eids.add(new)
            if new != current:
                elem.attrib['eId'] = new

    def resize_tables(self, doc):
        """ Ensure that tables have the correct number of columns and rows, otherwise
        PDF generation fails.
        """
        for table in doc.root.xpath('//a:table', namespaces={'a': doc.namespace}):
            # there should never be a completely empty row (FOP constraint)
            for empty_row in table.xpath('a:tr[not(a:td|a:th)]', namespaces={'a': doc.namespace}):
                table.remove(empty_row)
            # a cell can't span more rows than actually come after it (FOP constraint)
            for row in table.xpath('a:tr', namespaces={'a': doc.namespace}):
                actual = len(list(row.itersiblings(f'{{{doc.namespace}}}tr')))
                for cell in row.xpath('a:td[@rowspan] | a:th[@rowspan]', namespaces={'a': doc.namespace}):
                    rowspan = int(cell.get('rowspan', 1))
                    if rowspan > 1:
                        # rowspan is the smaller of the current rowspan, and the actual number of rows (plus this one)
                        cell.set('rowspan', str(min(rowspan, actual + 1)))

            matrix = self.map_table(table, doc)

            # max number of rows and columns
            n_rows = len(matrix)
            n_cols = max(len(row) for row in matrix.values()) if n_rows else 0

            # adjust rows
            missing_rows = n_rows - len(table.xpath('a:tr', namespaces={'a': doc.namespace}))
            for y in range(missing_rows):
                log.debug(f"Adding missing row in table {table.get('eId')}")
                table.append(doc.maker('tr'))

            # adjust cells
            for y, row in enumerate(table.xpath('a:tr', namespaces={'a': doc.namespace})):
                missing_cells = n_cols - len(matrix[y])
                for x in range(missing_cells):
                    log.debug(f"Adding missing cell in table {table.get('eId')} on row {y+1}")
                    cell = doc.maker('td')
                    cell.append(doc.maker('p'))
                    row.append(cell)
                # update the matrix
                for x in range(n_cols):
                    matrix[y][x] = True

            # add colgroup element with each column and its width
            column_widths = [0 for _ in range(n_cols)]
            # offset also needs to take rowspans into account: update the matrix to be False for co-ordinates where
            # a cell is not expected because of a rowspan on a previous cell
            for y, row in enumerate(table.xpath('a:tr', namespaces={'a': doc.namespace})):
                offset = 0
                for x, cell in enumerate(row.xpath('a:th|a:td', namespaces={'a': doc.namespace})):
                    # take colspan into account to set False on the correct cell in the matrix
                    colspan = int(cell.get('colspan', '1'))
                    offset += colspan - 1
                    rowspan = int(cell.get('rowspan', '1'))
                    if rowspan > 1:
                        for r in range(rowspan - 1):
                            matrix[y + 1 + r][x + offset] = False

            for y, row in enumerate(table.xpath('a:tr', namespaces={'a': doc.namespace})):
                # lets us derive the column from the current cell and all previously spanned columns in each row
                offset = 0
                for x, cell in enumerate(row.xpath('a:th|a:td', namespaces={'a': doc.namespace})):
                    # ignore cells with a colspan other than 1
                    # (assumes that if there is a colspan it's a positive integer)
                    colspan = int(cell.get('colspan', '1'))
                    offset += colspan - 1
                    # also increase offset if rowspan(s) in a previous row affect this row (indicated by a 'False' cell)
                    for col in range(n_cols):
                        # only check cells up to where we are currently
                        if col > x + offset:
                            break
                        if not matrix[y][col]:
                            offset += 1
                            # only count each 'False' cell once
                            matrix[y][col] = True
                    if colspan > 1:
                        continue

                    # ignore cells for which the column width has already been set
                    if column_widths[x + offset]:
                        continue

                    # set the width if there is one
                    cell_style = cell.get('style', '')
                    if cell_style.startswith('width:'):
                        try:
                            column_widths[x + offset] = math.floor(float(cell_style[6:].strip(' %;')))
                        except ValueError:
                            continue

            # if the total is > 100% and any columns are missing a width, just use defaults
            if sum(column_widths) > 100 and 0 in column_widths:
                column_widths = [0 for _ in range(n_cols)]

            # spread the remaining available space evenly between any columns that don't have a width
            # (including if none of them do)
            missing_width_indexes = [i for i, w in enumerate(column_widths) if not w]
            default_width = math.floor((100 - sum(column_widths)) / (len(missing_width_indexes) or 1))
            for i in missing_width_indexes:
                column_widths[i] = default_width

            # normalise columns so that total is 100%
            normalizr = 100 / sum(column_widths) if column_widths else 1
            for i, w in enumerate(column_widths):
                column_widths[i] = w * normalizr

            colgroup = doc.maker('colgroup')
            for width in column_widths:
                colgroup.append(doc.maker('col', width=f'{width}%'))

            # insert the colgroup at the top of the table
            table.insert(0, colgroup)

            # mark a table's first row as a table header if:
            # - all cells in it are header cells (th)
            # - the table has at least one other row (to go into the table body in FOP)
            # - no cells have a rowspan (FOP can't repeat half a row at the top of a page)
            # TODO: support multi-row table headers if the spanned rows are all headings too
            if n_rows > 1:
                for row in table.xpath('a:tr', namespaces={'a': doc.namespace}):
                    cells = row.xpath('./a:*', namespaces={'a': doc.namespace})
                    if all(cell.tag == f'{{{doc.namespace}}}th' for cell in cells) and not any(int(cell.get('rowspan', 1)) > 1 for cell in cells):
                        row.set('style', 'header-row')
                    # only check the first row
                    break

            # honour alignment
            for row in table.xpath('a:tr', namespaces={'a': doc.namespace}):
                for cell in row.xpath('a:th|a:td', namespaces={'a': doc.namespace}):
                    cell_class = cell.get('class')
                    if cell_class:
                        if 'akn--text-right' in cell_class:
                            cell.set('style', 'right')
                        elif 'akn--text-center' in cell_class:
                            cell.set('style', 'center')

            # set the table class to 'border', unless it has any cell with .akn--no-border
            if not list(table.xpath('.//a:*[contains(@class, "akn--no-border")]', namespaces={'a': doc.namespace})):
                table.set('class', 'border')

    def map_table(self, table, doc):
        """ Return a truth-table matrix for this table, where map[row][col] is True if a table cell covers it.

        See http://stackoverflow.com/questions/13407348/table-cellindex-and-rowindex-with-colspan-rowspan
        """

        def rows(t):
            return t.xpath('a:tr', namespaces={'a': doc.namespace})

        def cells(r):
            return r.xpath('a:td | a:th', namespaces={'a': doc.namespace})

        matrix = defaultdict(lambda: defaultdict(dict))
        for y, row in enumerate(rows(table)):
            for x, cell in enumerate(cells(row)):
                # skip already occupied cells in current row
                while matrix[y][x]:
                    x += 1

                # mark matrix elements occupied by current cell with true
                for xx in range(x, x + int(cell.get('colspan', 1))):
                    for yy in range(y, y + int(cell.get('rowspan', 1))):
                        # skip already occupied cells due to overlapping spans
                        xxx = xx
                        while matrix[yy][xxx]:
                            xxx += 1
                        matrix[yy][xxx] = True

        return matrix

    def find_xsl_fo(self, document):
        """ Return the filename of an XSL-FO template to use to render this document.

        The normal Django static file system is used to find the file. The first file found is used.
        """
        candidates = filename_candidates(document, prefix='xsl/fo/fo_', suffix='.xsl')
        best = find_best_static(candidates)
        if not best:
            raise ValueError("Couldn't find FO-XSLT file to use for %s, tried: %s" % (document, candidates))
        return best

    def update_base_xsl_fo_dir(self, xsl_fo):
        """ In the XSL FO, replace __INDIGO_API_XSL_DIR__ with the full path to indigo_api/static/xsl/fo.
            This will ensure that the base stylesheets are always available for import.
        """
        with open(xsl_fo, 'r+') as f:
            out = re.sub('__INDIGO_API_XSL_DIR__', self.base_xsl_fo_dir, f.read())
            f.truncate(0)
            f.seek(0)
            f.write(out)

    def final_tweaks(self, xml_str):
        # inline glyphs
        # TODO: do this in the XML rather than as a string replacement?
        for glyph in self.inline_glyphs:
            xml_str = xml_str.replace(glyph, f'<span class="inline-glyph">{glyph}</span>')
        return xml_str


class EPUBExporter(HTMLExporter):
    """ Helper to render documents as ePubs.

    The PipelineMixin lets us look up the raw content of the compiled
    CSS to inject into the epub.
    """
    # HTML tags that EPUB doesn't like
    BAD_DIV_TAG_RE = re.compile(r'(</?)(section)(\s+|>)', re.IGNORECASE)
    PATH_SUB_RE = re.compile(r'[^a-zA-Z0-9-_]')

    def __init__(self, colophon=True, *args, **kwargs):
        super(EPUBExporter, self).__init__(*args, **kwargs)
        self.colophon = colophon

    def render(self, document, element=None):
        self.create_book()

        self.book.set_identifier(document.expression_uri.expression_uri())
        self.book.set_title(document.title)
        self.book.set_language(document.language.language.iso)
        self.book.add_author(settings.INDIGO_ORGANISATION)

        if self.colophon:
            self.add_colophon(document=document)
        self.book.spine.append('nav')

        self.add_document(document)
        return self.to_epub()

    def render_many(self, documents):
        self.create_book()

        self.book.set_identifier(':'.join(d.expression_uri.expression_uri() for d in documents))
        self.book.add_author(settings.INDIGO_ORGANISATION)
        self.book.set_title('%d documents' % len(documents))

        # language
        langs = list(set(d.language.language.iso for d in documents))
        self.book.set_language(langs[0])
        for lang in langs[1:]:
            self.book.add_metadata('DC', 'language', lang)

        if self.colophon:
            self.add_colophon(documents=documents)
        self.book.spine.append('nav')

        for d in documents:
            self.add_document(d)

        return self.to_epub()

    def create_book(self):
        self.book = epub.EpubBook()
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())
        self.book.add_metadata('DC', 'publisher', settings.INDIGO_ORGANISATION)

    def add_css(self):
        self.stylesheets = []

        path = 'stylesheets/export-epub.css'
        static_path = find_static(path)
        if not static_path:
            # compile the scss, this is mostly only for unit tests, because the sass is compiled with compilescss
            # in production
            processor = SassProcessor()
            processor.processor_enabled = True
            static_path = find_static(processor('stylesheets/export-epub.scss'))

        with open(static_path) as f:
            css = f.read()
        self.book.add_item(epub.EpubItem(file_name=path, media_type="text/css", content=css))
        self.stylesheets.append(path)

        # now ensure all html items link to the stylesheets
        for item in self.book.items:
            if isinstance(item, (epub.EpubHtml, epub.EpubNav)):
                for stylesheet in self.stylesheets:
                    # relativise path
                    href = '/'.join(['..'] * item.file_name.count('/') + [stylesheet])
                    item.add_link(href=href, rel='stylesheet', type='text/css')

    def add_colophon(self, document, documents=None):
        colophon = self.find_colophon(document or documents[0])
        if colophon:
            html = self.clean_html(self.render_colophon(colophon, document, documents))

            # pull in any static images used in the colophon
            doc = ET.HTML(html)
            images = [img for img in doc.xpath('//img[@src]') if img.get('src').startswith('/static/')]
            # rewrite paths to be relative
            for img in images:
                img.set('src', img.get('src')[1:])
            html = ET.tostring(doc)

            entry = epub.EpubHtml(uid='colophon', file_name='colophon.xhtml')
            entry.content = html
            self.book.add_item(entry)
            self.book.spine.append(entry)

            for fname in set(img.get('src') for img in images):
                local_fname = find_static(fname[7:])
                if local_fname:
                    img = epub.EpubImage()
                    img.file_name = fname
                    with open(local_fname, 'rb') as f:
                        img.content = f.read()
                    self.book.add_item(img)

    def render_colophon(self, colophon, document, documents):
        # find the wrapper template
        candidates = filename_candidates(document, prefix='indigo_api/akn/export/epub_colophon_', suffix='.html')
        best = find_best_template(candidates)
        if not best:
            raise ValueError("Couldn't find colophon file for EPUB.")

        colophon_wrapper = get_template(best).origin.name
        return render_to_string(colophon_wrapper, {
            'colophon': colophon,
            'document': document,
            'documents': documents,
        })

    def add_document(self, document):
        # relative directory for files for this document
        file_dir = 'doc-%s' % document.id
        self.renderer = self._xml_renderer(document)

        titlepage = self.add_titlepage(document, file_dir)

        # generate the individual items for each navigable element
        children = []
        toc = document.table_of_contents()
        for item in toc:
            children.append(self.add_item(item, file_dir))

        # add everything as a child of this document
        self.book.toc.append((titlepage, children))

        # add images
        self.add_attachments(document, file_dir)

    def add_attachments(self, document, file_dir):
        fnames = set(
            img.get('src')[6:]
            for img in document.doc.root.xpath('//a:img[@src]', namespaces={'a': document.doc.namespace})
            if img.get('src', '').startswith('media/')
        )

        for attachment in document.attachments.all():
            if attachment.filename in fnames:
                img = epub.EpubImage()
                img.file_name = f'{file_dir}/media/{attachment.filename}'
                img.content = attachment.file.read()
                self.book.add_item(img)

    def add_titlepage(self, document, file_dir):
        # find the template to use
        template_name = self.template_name or self.find_template(document)
        context = {
            'document': document,
            'element': None,
            'content_html': '',
            'renderer': self.renderer,
            'coverpage': True,
            'resolver_url': self.resolver,
            'coverpage_template': self.coverpage_template(document),
        }
        titlepage = render_to_string(template_name, context)

        fname = os.path.join(file_dir, 'titlepage.xhtml')
        entry = epub.EpubHtml(title=document.title, uid='%s-titlepage' % file_dir, file_name=fname)
        entry.content = self.clean_html(titlepage, wrap='akoma-ntoso')

        self.book.add_item(entry)
        self.book.spine.append(entry)

        return entry

    def add_item(self, item, file_dir):
        id = self.item_id(item)
        fname = os.path.join(file_dir, self.PATH_SUB_RE.sub('_', id) + '.xhtml')

        entry = epub.EpubHtml(
            title=item.title,
            uid='-'.join([file_dir, id]),
            file_name=fname)
        entry.content = self.clean_html(self.renderer.render(item.element), wrap='akoma-ntoso')

        self.book.add_item(entry)
        self.book.spine.append(entry)

        # TOC entries
        def child_tocs(child):
            if child.id:
                us = epub.Link(fname + '#' + child.id, child.title, child.id)
            else:
                us = epub.Section(self.item_heading(child))

            if child.children:
                children = [child_tocs(c) for c in child.children]
                return [us, children]
            else:
                return us

        if item.children:
            return (entry, [child_tocs(c) for c in item.children])
        else:
            return entry

    def to_epub(self):
        self.add_css()

        with tempfile.NamedTemporaryFile(suffix='.epub') as f:
            epub.write_epub(f.name, self.book, {})
            return f.read()

    def item_id(self, item):
        parts = [item.component]

        id = item.id
        if not id:
            parts.append(item.type)
            parts.append(item.num)
        else:
            parts.append(id)

        return '-'.join([p for p in parts if p])

    def clean_html(self, html, wrap=None):
        html = self.BAD_DIV_TAG_RE.sub('\\1div\\3', str(html))
        if wrap:
            html = '<div class="' + wrap + '">' + html + '</div>'
        return html

    def language_for(self, lang):
        lang = Language.objects.filter(iso_639_2T=lang).first()
        if lang:
            return lang.iso


class XSLTRenderer(object):
    """ Renders an Akoma Ntoso Act XML document using XSL transforms.
    """

    def __init__(self, xslt_filename, xslt_params=None):
        self.xslt = ET.XSLT(ET.parse(xslt_filename))
        self.xslt_params = xslt_params or {}

    def render(self, node):
        """ Render an XML Tree or Element object into an HTML string.
        """
        params = {k: ET.XSLT.strparam(v) for k, v in self.xslt_params.items()}
        return ET.tostring(self.xslt(node, **params), encoding='unicode')

    def render_xml(self, xml):
        """ Render an XML string into an HTML string.
        """
        if isinstance(xml, str):
            xml = xml.encode('utf-8')
        return self.render(ET.fromstring(xml))
