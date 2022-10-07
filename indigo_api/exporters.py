import os
import re
import shutil
import tempfile
import urllib.parse
import logging
import subprocess

import lxml.html
from django.conf import settings
from django.contrib.staticfiles.finders import find as find_static
from django.template.loader import render_to_string, get_template
from ebooklib import epub
from languages_plus.models import Language
from lxml import etree as ET
from sass_processor.processor import SassProcessor
from wkhtmltopdf import make_absolute_paths, wkhtmltopdf

from indigo.plugins import plugins, LocaleBasedMatcher
from indigo_api.models import Colophon
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
    """ Exports (renders) AKN documents as PDFs.
    """
    locale = (None, None, None)

    def __init__(self, toc=True, colophon=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.toc = toc
        self.colophon = colophon

    def render(self, document, element=None):
        self.media_url = 'doc-0/'
        html = super().render(document, element=element)

        # embed the HTML into the PDF container
        html = render_to_string('indigo_api/akn/export/pdf.html', {
            'documents': [(document, html)],
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            html = self.save_attachments(html, document, 'doc-0/media/', tmpdir)
            return self.to_pdf(html, tmpdir, document=document)

    def render_many(self, documents, **kwargs):
        html = []

        with tempfile.TemporaryDirectory() as tmpdir:
            # render individual documents
            for i, doc in enumerate(documents):
                self.media_url = f'doc-{i}/'
                doc_html = super().render(doc, **kwargs)
                self.save_attachments(doc_html, doc, f'doc-{i}/media/', tmpdir)

                html.append(doc_html)

            # combine and embed the HTML into the PDF container
            html = render_to_string('indigo_api/akn/export/pdf.html', {
                'documents': list(zip(documents, html)),
            })

            return self.to_pdf(html, tmpdir, documents=documents)

    def save_attachments(self, html, document, prefix, tmpdir):
        """ Place attachments needed by the html of this document into tmpdir. Only attachments
        referenced using the given prefix are saved.
        """
        html = lxml.html.fromstring(html)
        prefix_len = len(prefix)

        # gather up the attachments that occur in the html
        imgs = [img for img in html.iter('img') if img.get('src', '').startswith(prefix)]
        fnames = set(img.get('src')[prefix_len:] for img in imgs)

        # ensure the media directory exists
        media_dir = os.path.join(tmpdir, prefix)
        os.makedirs(media_dir, exist_ok=True)

        for attachment in document.attachments.all():
            # the src attribute values in fnames are URL-quoted
            if urllib.parse.quote(attachment.filename) in fnames:
                # save the attachment into tmpdir
                fname = os.path.join(media_dir, attachment.filename)
                with open(fname, "wb") as f:
                    shutil.copyfileobj(attachment.file, f)

        # make img references absolute
        # see https://github.com/wkhtmltopdf/wkhtmltopdf/issues/2660
        for img in imgs:
            img.set('src', os.path.join(tmpdir, img.get('src')))

        return lxml.html.tostring(html, encoding='unicode')

    def to_pdf(self, html, dirname, document=None, documents=None):
        options = self.pdf_options()
        args = [
            '--allow', dirname,
            '--allow', settings.MEDIA_ROOT,
            '--allow', settings.STATIC_ROOT,
        ]

        # for debugging, an array of (filename, content) tuples
        files = []

        # this makes all paths, such as stylesheets and javascript, use
        # absolute file paths so that wkhtmltopdf finds them
        html = make_absolute_paths(html)

        # keep this around so that the file doesn't get cleaned up
        # before it's used
        colophon_f = None
        if self.colophon:
            colophon = self.render_colophon(document=document, documents=documents)
            if colophon:
                colophon_f = tempfile.NamedTemporaryFile(suffix='.html')
                colophon_f.write(colophon.encode('utf-8'))
                colophon_f.flush()
                args.extend(['cover', 'file://' + colophon_f.name])
                files.append((colophon_f.name, colophon))

        toc_xsl = options.pop('xsl-style-sheet')
        if self.toc:
            args.extend(['toc', '--xsl-style-sheet', toc_xsl])

        with tempfile.NamedTemporaryFile(suffix='.html', dir=dirname) as f:
            f.write(html.encode('utf-8'))
            f.flush()
            args.append('file://' + f.name)
            files.append((f.name, html))

            try:
                return self._wkhtmltopdf(args, **options)
            except subprocess.CalledProcessError as e:
                files = '\n'.join(f'{name}:\n---\n{value}\n---' for name, value in files)
                log.warning(f"wkhtmltopdf failed. args: {args}. options: {options}. files: \n{files}")
                raise

    def render_colophon(self, document=None, documents=None):
        """ Find the colophon template this document and render it, returning
        the rendered HTML. This renders the colophon using a wrapper
        template to ensure it's a full HTML document.
        """
        colophon = self.find_colophon(document or documents[0])
        if colophon:
            # find the wrapper template
            candidates = filename_candidates(self.document, prefix='indigo_api/akn/export/pdf_colophon_', suffix='.html')
            best = find_best_template(candidates)
            if not best:
                raise ValueError("Couldn't find colophon file for PDF.")

            colophon_wrapper = get_template(best).origin.name
            html = render_to_string(colophon_wrapper, {
                'colophon': colophon,
                'document': document,
                'documents': documents,
            })
            return make_absolute_paths(html)

    def _wkhtmltopdf(self, *args, **kwargs):
        # wkhtmltopdf sometimes fails with a transient error, so try multiple times
        attempts = 0
        while True:
            try:
                attempts += 1
                return wkhtmltopdf(*args, **kwargs)
            except subprocess.CalledProcessError as e:
                if attempts < 3:
                    log.info("Retrying after wkhtmltopdf error")
                else:
                    raise e

    def pdf_options(self):
        # See https://eegg.wordpress.com/2010/01/25/page-margins-in-principle-and-practice/
        # for background on the two circle canon for calculating margins for an A4 page.
        #
        # To calculate margins for a page of width W and height H, plug the following
        # equation into Wolfram Alpha, and read off the smaller of the two pairs of
        # values for s (the side margin) and t (the top/bottom margin) in mm.
        #
        # y=Mx; (x-W/2)^2+(y-(H-W/2))^2=(W/2)^2; s=W-x; t=H-y; M = H/W; H=297; W=210
        #
        # or use this link: http://wolfr.am/8BoqtzV5
        #
        # Target margins are: 36.3mm (top, bottom); 25.6mm (left, right)
        # We want to pull the footer (7.5mm high) into the margin, so we decrease
        # the margin slightly

        header_font = 'Georgia, "Times New Roman", serif'
        header_font_size = '8'
        header_spacing = 5
        margin_top = 36.3 - header_spacing
        margin_bottom = 36.3 - header_spacing
        margin_left = 25.6

        options = {
            'page-size': 'A4',
            'margin-top': '%.2fmm' % margin_top,
            'margin-bottom': '%2.fmm' % margin_bottom,
            'margin-left': '%.2fmm' % margin_left,
            'margin-right': '%.2fmm' % margin_left,
            'header-left': '[section]',
            'header-spacing': '%.2f' % header_spacing,
            'header-right': self.document.work.place.name,
            'header-font-name': header_font,
            'header-font-size': header_font_size,
            'header-line': True,
            'footer-html': self.footer_html(),
            'footer-line': True,
            'footer-spacing': '%.2f' % header_spacing,
            'xsl-style-sheet': self.toc_xsl(),
        }

        return options

    def toc_xsl(self):
        candidates = filename_candidates(self.document, prefix='indigo_api/akn/export/pdf_toc_', suffix='.xsl')
        best = find_best_template(candidates)
        if not best:
            raise ValueError("Couldn't find TOC XSL file for PDF.")
        return get_template(best).origin.name

    def footer_html(self):
        candidates = filename_candidates(self.document, prefix='indigo_api/akn/export/pdf_footer_', suffix='.html')
        best = find_best_template(candidates)
        if not best:
            raise ValueError("Couldn't find footer file for PDF.")
        return get_template(best).origin.name


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
        return str(self.xslt(node, **params))

    def render_xml(self, xml):
        """ Render an XML string into an HTML string.
        """
        if not isinstance(xml, str):
            xml = xml.decode('utf-8')
        return self.render(ET.fromstring(xml))
