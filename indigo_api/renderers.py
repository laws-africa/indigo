import lxml.etree as ET
import tempfile
import re
import os.path
import zipfile
import logging

from django.template.loader import get_template, render_to_string, TemplateDoesNotExist
from django.core.cache import caches
from django.conf import settings
from django.contrib.staticfiles.finders import find as find_static
from rest_framework.renderers import BaseRenderer, StaticHTMLRenderer
from rest_framework_xml.renderers import XMLRenderer
from wkhtmltopdf.utils import make_absolute_paths, wkhtmltopdf
from ebooklib import epub
from languages_plus.models import Language
from sass_processor.processor import SassProcessor

from .serializers import NoopSerializer
from .models import Document, Colophon

log = logging.getLogger(__name__)


def file_candidates(document, prefix='', suffix=''):
    """ Candidate files to use for this document.

    This takes into account the country, type, subtype and language of the document,
    providing a number of opportunities to adjust the rendering logic.

    The following templates are looked for, in order:

    * doctype-subtype-language-country
    * doctype-subtype-language
    * doctype-subtype-country
    * doctype-subtype
    * doctype-language-country
    * doctype-country
    * doctype-language
    * doctype
    """
    uri = document.doc.frbr_uri
    doctype = uri.doctype
    language = uri.language
    country = uri.country
    subtype = uri.subtype

    options = []
    if subtype:
        options.append('-'.join([doctype, subtype, language, country]))
        options.append('-'.join([doctype, subtype, language]))
        options.append('-'.join([doctype, subtype, country]))
        options.append('-'.join([doctype, subtype]))

    options.append('-'.join([doctype, language, country]))
    options.append('-'.join([doctype, country]))
    options.append('-'.join([doctype, language]))
    options.append(doctype)

    return [prefix + f + suffix for f in options]


def resolver_url(request, resolver):
    if resolver in ['no', 'none']:
        return ''

    if resolver:
        if resolver.startswith('http'):
            return resolver
        else:
            return request.build_absolute_uri('/resolver/%s/resolve' % resolver)

    return settings.RESOLVER_URL


class XSLTRenderer(object):
    """ Renders an Akoma Ntoso Act XML document using XSL transforms.
    """

    def __init__(self, xslt_filename, xslt_params=None):
        self.xslt = ET.XSLT(ET.parse(xslt_filename))
        self.xslt_params = xslt_params or {}

    def render(self, node):
        """ Render an XML Tree or Element object into an HTML string """
        params = {
            'defaultIdScope': ET.XSLT.strparam(self.defaultIdScope(node) or ''),
        }
        params.update({k: ET.XSLT.strparam(v) for k, v in self.xslt_params.iteritems()})
        return ET.tostring(self.xslt(node, **params))

    def render_xml(self, xml):
        """ Render an XML string into an HTML string """
        if not isinstance(xml, str):
            xml = xml.encode('utf-8')
        return self.render(ET.fromstring(xml))

    def defaultIdScope(self, node):
        """ Default scope for ID attributes when rendering.
        """
        ns = node.nsmap[None]
        scope = node.xpath('./ancestor::a:doc[@name][1]/@name', namespaces={'a': ns})
        if scope:
            return scope[0]


def generate_filename(data, view, format=None):
    if isinstance(data, Document):
        parts = [data.year, data.number]
        if hasattr(view, 'component'):
            parts.extend([view.component if view.component != 'main' else None, view.subcomponent])
    else:
        parts = view.kwargs['frbr_uri'].split('/')

    parts = [re.sub('[/ .]', '-', p) for p in parts if p]
    fname = '-'.join(parts)
    if format:
        fname += '.' + format

    return fname


class AkomaNtosoRenderer(XMLRenderer):
    """ Django Rest Framework Akoma Ntoso Renderer.
    """
    serializer_class = NoopSerializer

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, Document):
            return super(AkomaNtosoRenderer, self).render(data, media_type, renderer_context)

        view = renderer_context['view']
        filename = generate_filename(data, view, self.format)
        renderer_context['response']['Content-Disposition'] = 'attachment; filename=%s' % filename

        if not hasattr(view, 'component') or (view.component == 'main' and not view.subcomponent):
            return data.document_xml

        return ET.tostring(view.element, pretty_print=True)


class HTMLRenderer(object):
    """ Render documents as as HTML.
    """
    def __init__(self, coverpage=True, standalone=False, template_name=None, no_stub_content=False, resolver=None):
        self.template_name = template_name
        self.standalone = standalone
        self.coverpage = coverpage
        self.no_stub_content = no_stub_content
        self.resolver = resolver or settings.RESOLVER_URL
        self.media_url = ''

    def render(self, document, element=None):
        """ Render this document to HTML.

        :param document: document to render if +element+ is None
        :param element: element to render (optional)
        """
        # use this to render the bulk of the document
        renderer = self._xml_renderer(document)

        if element is not None:
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
            'resolver_url': self.resolver,
        }

        # Now render some boilerplate around it.
        if self.standalone:
            context['template_name'] = template_name
            context['colophon'] = self.find_colophon(document)
            return render_to_string('export/standalone.html', context)
        else:
            return render_to_string(template_name, context)

    def find_colophon(self, document):
        return Colophon.objects.filter(country=document.work.country).first()

    def find_template(self, document):
        """ Return the filename of a template to use to render this document.

        The normal Django templating system is used to find a template. The first template
        found is used.
        """
        candidates = file_candidates(document, suffix='.html')
        for option in candidates:
            try:
                log.debug("Looking for %s" % option)
                if get_template(option):
                    log.debug("Using template %s" % option)
                    return option
            except TemplateDoesNotExist:
                pass

        raise ValueError("Couldn't find an HTML template to use for %s, tried: %s" % (document, candidates))

    def find_xslt(self, document):
        """ Return the filename of an xslt template to use to render this document.

        The normal Django templating system is used to find a template. The first template
        found is used.
        """
        candidates = file_candidates(document, prefix='xsl/', suffix='.xsl')
        for option in candidates:
            log.debug("Looking for %s" % option)
            fname = find_static(option)
            if fname:
                log.debug("Using xsl %s" % fname)
                return fname

        raise ValueError("Couldn't find XSLT file to use for %s, tried: %s" % (document, candidates))

    def _xml_renderer(self, document):
        params = {
            'resolverUrl': self.resolver,
            'mediaUrl': self.media_url or '',
            'lang': document.language.code,
        }

        return XSLTRenderer(xslt_params=params, xslt_filename=self.find_xslt(document))


class HTMLResponseRenderer(StaticHTMLRenderer):
    serializer_class = NoopSerializer

    def render(self, document, media_type=None, renderer_context=None):
        if not isinstance(document, Document):
            return super(HTMLResponseRenderer, self).render(document, media_type, renderer_context)

        view = renderer_context['view']
        request = renderer_context['request']

        renderer = HTMLRenderer()
        renderer.no_stub_content = getattr(view, 'no_stub_content', False)
        renderer.standalone = request.GET.get('standalone') == '1'
        renderer.resolver = resolver_url(request, request.GET.get('resolver'))
        renderer.media_url = request.GET.get('media-url', '')

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
                colophon_f.write(colophon.encode('utf-8'))
                colophon_f.flush()
                args.extend(['cover', 'file://' + colophon_f.name])

        toc_xsl = options.pop('xsl-style-sheet')
        if self.toc:
            args.extend(['toc', '--xsl-style-sheet', toc_xsl])

        with tempfile.NamedTemporaryFile(suffix='.html') as f:
            f.write(html.encode('utf-8'))
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

        toc_xsl = get_template('export/pdf_toc.xsl').origin.name

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
            'xsl-style-sheet': toc_xsl,
        }

        return options


class EPUBRenderer(HTMLRenderer):
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
        self.book.set_language(document.language.language.iso)
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
        langs = list(set(d.language.language.iso for d in documents))
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
        self.stylesheets = []

        # compile scss and add the file
        processor = SassProcessor()
        processor.processor_enabled = True
        path = processor('stylesheets/epub.scss')
        with processor.storage.open(path) as f:
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
        toc = document.table_of_contents()
        for item in toc:
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
            'resolver_url': self.resolver,
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

    def language_for(self, lang):
        lang = Language.objects.filter(iso_639_2T=lang).first()
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
        self.cache = caches['default']

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, (Document, list)):
            return ''

        view = renderer_context['view']
        filename = self.get_filename(data, view)
        renderer_context['response']['Content-Disposition'] = 'inline; filename=%s' % filename
        request = renderer_context['request']

        renderer = PDFRenderer()
        renderer.no_stub_content = getattr(renderer_context['view'], 'no_stub_content', False)
        renderer.resolver = resolver_url(request, request.GET.get('resolver'))

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
        return generate_filename(data, view, self.format)


class EPUBResponseRenderer(PDFResponseRenderer):
    """ Django Rest Framework ePub Renderer.
    """
    media_type = 'application/epub+zip'
    format = 'epub'

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, (Document, list)):
            return ''

        view = renderer_context['view']
        request = renderer_context['request']

        filename = self.get_filename(data, view)
        renderer_context['response']['Content-Disposition'] = 'inline; filename=%s' % filename
        renderer = EPUBRenderer()
        renderer.no_stub_content = getattr(renderer_context['view'], 'no_stub_content', False)
        renderer.resolver = resolver_url(request, request.GET.get('resolver'))

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


class ZIPResponseRenderer(BaseRenderer):
    """ Django Rest Framework zipfile renderer.

    Generates a zip file containing the primary document as main.xml, an all attachments
    inside a media folder.
    """
    media_type = 'application/zip'
    format = 'zip'
    serializer_class = NoopSerializer

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, (Document, list)):
            return ''

        view = renderer_context['view']
        filename = generate_filename(data, view, self.format)
        renderer_context['response']['Content-Disposition'] = 'attachment; filename=%s' % filename

        with tempfile.NamedTemporaryFile(suffix='.zip') as f:
            self.build_zipfile(data, f.name)
            return f.read()

    def build_zipfile(self, data, fname):
        # one or many documents?
        many = isinstance(data, list)
        if not many:
            data = [data]

        with zipfile.ZipFile(fname, 'w', zipfile.ZIP_DEFLATED) as zf:
            for document in data:
                # if storing many, prefix them
                prefix = (generate_filename(document, None) + '/') if many else ''
                zf.writestr(prefix + "main.xml", document.document_xml.encode('utf-8'))

                for attachment in document.attachments.all():
                    zf.writestr(prefix + "media/" + attachment.filename, attachment.file.read())
