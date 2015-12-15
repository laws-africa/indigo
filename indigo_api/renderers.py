import lxml.etree as ET
import tempfile
import re
import os.path
import codecs

from django.template.loader import find_template, render_to_string, TemplateDoesNotExist
from django.core.cache import get_cache
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings
from rest_framework.renderers import BaseRenderer, StaticHTMLRenderer
from rest_framework_xml.renderers import XMLRenderer
from wkhtmltopdf.utils import make_absolute_paths, wkhtmltopdf
from ebooklib import epub
from pipeline.templatetags.pipeline import PipelineMixin
from pipeline.collector import default_collector
from pipeline.packager import Packager
from languages_plus.models import Language

from cobalt.render import HTMLRenderer as CobaltHTMLRenderer
from .serializers import NoopSerializer
from .models import Document, Colophon, DEFAULT_LANGUAGE


class AkomaNtosoRenderer(XMLRenderer):
    """ Django Rest Framework Akoma Ntoso Renderer.
    """
    serializer_class = NoopSerializer

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, Document):
            return super(AkomaNtosoRenderer, self).render(data, media_type, renderer_context)

        view = renderer_context['view']
        if view.component == 'main' and not view.subcomponent:
            return data.document_xml

        return ET.tostring(view.element, pretty_print=True)


class HTMLRenderer(object):
    """ Render documents as as HTML.
    """
    def __init__(self, coverpage=True, standalone=False, template_name=None, cobalt_kwargs=None, no_stub_content=False):
        self.template_name = template_name
        self.standalone = standalone
        self.cobalt_kwargs = cobalt_kwargs or {}
        self.coverpage = coverpage
        self.no_stub_content = no_stub_content

    def render(self, document, element=None):
        """ Render this document to HTML.

        :param document: document to render if +element+ is None
        :param element: element to render (optional)
        """
        # use this to render the bulk of the document with the Cobalt XSLT renderer
        renderer = self._xml_renderer(document)

        if element:
            # just a fragment of the document
            content_html = renderer.render(element)
            if not self.standalone:
                # we're done
                return content_html
        elif self.no_stub_content and document.stub:
            # Stub
            content_html = ''
        else:
            # the entire document
            content_html = renderer.render_xml(document.document_xml)

        # find the template to use
        template_name = self.template_name or self.find_template(document)

        context = {
            'document': document,
            'element': element,
            'content_html': content_html,
            'renderer': renderer,
            'coverpage': self.coverpage,
        }

        # Now render some boilerplate around it.
        if self.standalone:
            context['template_name'] = template_name
            context['colophon'] = self.find_colophon(document)
            return render_to_string('export/standalone.html', context)
        else:
            return render_to_string(template_name, context)

    def find_colophon(self, document):
        colophon = None

        if document.country:
            colophon = Colophon.objects.filter(country__iso=document.country.upper()).first()

        if not colophon:
            colophon = Colophon.objects.filter(country=None).first()

        return colophon

    def find_template(self, document, prefix=''):
        """ Return the filename of a template to use to render this document.

        This takes into account the country, type, subtype and language of the document,
        providing a number of opportunities to adjust the rendering logic.

        The normal Django templating system is used to find a template. The first template
        found is used. The following templates are looked for, in order:

        * doctype_subtype_language_country.html
        * doctype_subtype_country.html
        * doctype_subtype_language.html
        * doctype_country.html
        * doctype_subtype.html
        * doctype_language_country.html
        * doctype_country.html
        * doctype_language.html
        * doctype.html
        """
        uri = document.doc.frbr_uri
        doctype = uri.doctype

        options = []
        if uri.subtype:
            options.append('_'.join([doctype, uri.subtype, document.language, uri.country]))
            options.append('_'.join([doctype, uri.subtype, uri.country]))
            options.append('_'.join([doctype, uri.subtype, document.language]))
            options.append('_'.join([doctype, uri.country]))
            options.append('_'.join([doctype, uri.subtype]))

        options.append('_'.join([doctype, document.language, uri.country]))
        options.append('_'.join([doctype, uri.country]))
        options.append('_'.join([doctype, document.language]))
        options.append(doctype)

        options = [prefix + f + '.html' for f in options]

        for option in options:
            try:
                if find_template(option):
                    return option
            except TemplateDoesNotExist:
                pass

        raise ValueError("Couldn't find a template to use for %s. Tried: %s" % (uri, ', '.join(options)))

    def _xml_renderer(self, document):
        return CobaltHTMLRenderer(act=document.doc, **self.cobalt_kwargs)


class HTMLResponseRenderer(StaticHTMLRenderer):
    serializer_class = NoopSerializer

    def render(self, document, media_type=None, renderer_context=None):
        if not isinstance(document, Document):
            return super(HTMLResponseRenderer, self).render(document, media_type, renderer_context)

        view = renderer_context['view']
        renderer = HTMLRenderer()
        renderer.no_stub_content = getattr(renderer_context['view'], 'no_stub_content', False)
        renderer.standalone = renderer_context['request'].GET.get('standalone') == '1'

        if not hasattr(view, 'component') or (view.component == 'main' and not view.subcomponent):
            renderer.coverpage = renderer_context['request'].GET.get('coverpage', '1') == '1'
            return renderer.render(document)

        renderer.coverpage = renderer_context['request'].GET.get('coverpage') == '1'
        return renderer.render(document, view.element)


class PDFRenderer(HTMLRenderer):
    """ Helper to render documents as PDFs.
    """
    def __init__(self, toc=True, colophon=True, *args, **kwargs):
        super(PDFRenderer, self).__init__(*args, **kwargs)
        self.toc = toc
        self.colophon = colophon

    def render(self, document, element=None):
        html = super(PDFRenderer, self).render(document, element=element)

        # embed the HTML into the PDF container
        html = render_to_string('export/pdf.html', {
            'documents': [(document, html)],
        })
        return self.to_pdf(html, document=document)

    def render_many(self, documents, **kwargs):
        html = []

        for doc in documents:
            html.append(super(PDFRenderer, self).render(doc, **kwargs))

        # embed the HTML into the PDF container
        html = render_to_string('export/pdf.html', {
            'documents': zip(documents, html),
        })
        return self.to_pdf(html, documents=documents)

    def to_pdf(self, html, document=None, documents=None):
        args = []
        options = self.pdf_options()

        # this makes all paths, such as stylesheets and javascript, use
        # absolute file paths so that wkhtmltopdf finds them
        html = make_absolute_paths(html)

        # keep this around so that the file doesn't get cleaned up
        # before its used
        colophon_f = None
        if self.colophon:
            colophon = self.render_colophon(document=document, documents=documents)
            if colophon:
                colophon_f = tempfile.NamedTemporaryFile(suffix='.html')
                colophon_f.write(colophon)
                colophon_f.flush()
                args.extend(['cover', 'file://' + colophon_f.name])

        toc_xsl = options.pop('xsl-style-sheet')
        if self.toc:
            args.extend(['toc', '--xsl-style-sheet', toc_xsl])

        with tempfile.NamedTemporaryFile(suffix='.html') as f:
            f.write(html)
            f.flush()
            args.append('file://' + f.name)
            return self._wkhtmltopdf(args, **options)

    def render_colophon(self, document=None, documents=None):
        """ Find the colophon template this document and render it, returning
        the rendered HTML. This renders the colophon using a wrapper
        template to ensure it's a full HTML document.
        """
        colophon = self.find_colophon(document or documents[0])
        if colophon:
            # find the wrapper template
            html = render_to_string('export/pdf_colophon.html', {
                'colophon': colophon,
            })
            return make_absolute_paths(html)

    def _wkhtmltopdf(self, *args, **kwargs):
        return wkhtmltopdf(*args, **kwargs)

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

        footer_font = 'Georgia, "Times New Roman", serif'
        footer_font_size = '10'
        footer_spacing = 5
        margin_top = 36.3 - footer_spacing
        margin_bottom = 36.3 - footer_spacing
        margin_left = 25.6

        options = {
            'page-size': 'A4',
            'margin-top': '%.2fmm' % margin_top,
            'margin-bottom': '%2.fmm' % margin_bottom,
            'margin-left': '%.2fmm' % margin_left,
            'margin-right': '%.2fmm' % margin_left,
            'header-left': '[section]',
            'header-spacing': '%.2f' % footer_spacing,
            'header-font-name': footer_font,
            'header-font-size': footer_font_size,
            'header-line': True,
            'footer-center': '[page] of [toPage]',
            'footer-spacing': '%.2f' % footer_spacing,
            'footer-font-name': footer_font,
            'footer-font-size': footer_font_size,
            'xsl-style-sheet': os.path.abspath('indigo_api/templates/export/pdf_toc.xsl'),
        }

        return options


class EPUBRenderer(PipelineMixin, HTMLRenderer):
    """ Helper to render documents as ePubs.

    The PipelineMixin lets us look up the raw content of the compiled
    CSS to inject into the epub.
    """
    # HTML tags that EPUB doesn't like
    BAD_DIV_TAG_RE = re.compile(r'(</?)(section)(\s+|>)', re.IGNORECASE)
    PATH_SUB_RE = re.compile(r'[^a-zA-Z0-9-_]')

    def __init__(self, *args, **kwargs):
        super(EPUBRenderer, self).__init__(*args, **kwargs)

    def render(self, document, element=None):
        self.create_book()

        self.book.set_identifier(document.doc.frbr_uri.expression_uri())
        self.book.set_title(document.title)
        self.book.set_language(self.language_for(document.language) or 'en')
        self.book.add_author(settings.INDIGO_ORGANISATION)

        self.add_colophon(document)
        self.book.spine.append('nav')

        self.add_document(document)
        return self.to_epub()

    def render_many(self, documents):
        self.create_book()

        self.book.set_identifier(':'.join(d.doc.frbr_uri.expression_uri() for d in documents))
        self.book.add_author(settings.INDIGO_ORGANISATION)
        self.book.set_title('%d documents' % len(documents))

        # language
        langs = list(set(self.language_for(d.language) or 'en' for d in documents))
        self.book.set_language(langs[0])
        for lang in langs[1:]:
            self.book.add_metadata('DC', 'language', lang)

        self.add_colophon(documents[0])
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
        # compile assets
        default_collector.collect(self.request)

        # add the files that produce export.css
        pkg = self.package_for('epub', 'css')
        packager = Packager()
        paths = packager.compile(pkg.paths)

        self.stylesheets = []
        for path in paths:
            with codecs.open(staticfiles_storage.path(path), 'r', 'utf-8') as f:
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

    def add_colophon(self, document):
        colophon = self.find_colophon(document)
        if colophon:
            entry = epub.EpubHtml(uid='colophon', file_name='colophon.xhtml')
            entry.content = self.clean_html(colophon.body, wrap='colophon')
            self.book.add_item(entry)
            self.book.spine.append(entry)

    def add_document(self, document):
        # relative directory for files for this document
        file_dir = 'doc-%s' % document.id
        self.renderer = self._xml_renderer(document)

        titlepage = self.add_titlepage(document, file_dir)

        # generate the individual items for each navigable element
        children = []
        for item in document.doc.table_of_contents():
            children.append(self.add_item(item, file_dir))

        # add everything as a child of this document
        self.book.toc.append((titlepage, children))

    def add_titlepage(self, document, file_dir):
        # find the template to use
        template_name = self.template_name or self.find_template(document)
        context = {
            'document': document,
            'element': None,
            'content_html': '',
            'renderer': self.renderer,
            'coverpage': True,
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

        id = item.id or item.subcomponent
        if not id:
            parts.append(item.type)
            parts.append(item.num)
        else:
            parts.append(id)

        return '-'.join([p for p in parts if p])

    def clean_html(self, html, wrap=None):
        html = self.BAD_DIV_TAG_RE.sub('\\1div\\3', html)
        if wrap:
            html = '<div class="' + wrap + '">' + html + '</div>'
        return html

    def language_for(self, lang=None):
        lang = Language.objects.filter(iso_639_2T=lang or DEFAULT_LANGUAGE).first()
        if lang:
            return lang.iso


class PDFResponseRenderer(BaseRenderer):
    """ Django Rest Framework PDF Renderer.
    """
    media_type = 'application/pdf'
    format = 'pdf'
    serializer_class = NoopSerializer

    def __init__(self, *args, **kwargs):
        super(PDFResponseRenderer, self).__init__(*args, **kwargs)
        self.cache = get_cache('default')

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, (Document, list)):
            return ''

        view = renderer_context['view']

        filename = self.get_filename(data, view)
        renderer_context['response']['Content-Disposition'] = 'inline; filename=%s' % filename
        renderer = PDFRenderer()
        renderer.no_stub_content = getattr(renderer_context['view'], 'no_stub_content', False)

        # check the cache
        key = self.cache_key(data, view)
        if key:
            pdf = self.cache.get(key)
            if pdf:
                return pdf

        if isinstance(data, list):
            # render many
            pdf = renderer.render_many(data)
        elif not hasattr(view, 'component') or (view.component == 'main' and not view.subcomponent):
            # whole document
            pdf = renderer.render(data)
        else:
            # just one element
            renderer.toc = False
            pdf = renderer.render(data, view.element)

        # cache it
        if key:
            self.cache.set(key, pdf)

        return pdf

    def cache_key(self, data, view):
        if isinstance(data, Document):
            # it's unsaved, don't bother
            if data.id is None:
                return None

            parts = [data.id, data.updated_at.isoformat()]
            if hasattr(view, 'component'):
                parts.append(view.component)
                parts.append(view.subcomponent)
        else:
            # list of docs
            data = sorted(data, key=lambda d: d.id)
            parts = [(p.id, p.updated_at.isoformat()) for p in data]

        return [self.format] + parts

    def get_filename(self, data, view):
        if isinstance(data, Document):
            parts = [data.year, data.number]
            if hasattr(view, 'component'):
                parts.extend([view.component if view.component != 'main' else None, view.subcomponent])
        else:
            parts = view.kwargs['frbr_uri'].split('/')

        parts = [re.sub('[/ .]', '-', p) for p in parts if p]

        return '-'.join(parts) + '.' + self.format


class EPUBResponseRenderer(PDFResponseRenderer):
    """ Django Rest Framework ePub Renderer.
    """
    media_type = 'application/epub+zip'
    format = 'epub'

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, (Document, list)):
            return ''

        view = renderer_context['view']

        filename = self.get_filename(data, view)
        renderer_context['response']['Content-Disposition'] = 'inline; filename=%s' % filename
        renderer = EPUBRenderer()
        renderer.no_stub_content = getattr(renderer_context['view'], 'no_stub_content', False)

        # check the cache
        key = self.cache_key(data, view)
        if key:
            epub = self.cache.get(key)
            if epub:
                return epub

        if isinstance(data, list):
            # render many
            epub = renderer.render_many(data)
        elif not hasattr(view, 'component') or (view.component == 'main' and not view.subcomponent):
            # whole document
            epub = renderer.render(data)
        else:
            # just one element
            renderer.toc = False
            epub = renderer.render(data, view.element)

        # cache it
        if key:
            self.cache.set(key, epub)

        return epub
