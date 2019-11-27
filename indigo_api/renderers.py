import lxml.etree as ET
import lxml.html
import tempfile
import re
import os
import os.path
import zipfile
import logging
import shutil
import urllib.parse

from django.template.loader import get_template, render_to_string
from django.core.cache import caches
from django.conf import settings
from rest_framework.renderers import BaseRenderer, StaticHTMLRenderer
from rest_framework_xml.renderers import XMLRenderer
from wkhtmltopdf.utils import make_absolute_paths, wkhtmltopdf
from ebooklib import epub
from languages_plus.models import Language
from sass_processor.processor import SassProcessor

from indigo_api.utils import find_best_template, find_best_static, filename_candidates
from .serializers import NoopSerializer
from .models import Colophon

log = logging.getLogger(__name__)


def resolver_url(request, resolver):
    if resolver in ['no', 'none']:
        return ''

    if resolver:
        if resolver.startswith('http') or resolver.startswith('/'):
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
        """ Render an XML Tree or Element object into an HTML string.
        """
        params = {
            'defaultIdScope': ET.XSLT.strparam(self.defaultIdScope(node) or ''),
        }
        params.update({k: ET.XSLT.strparam(v) for k, v in self.xslt_params.items()})
        return str(self.xslt(node, **params))

    def render_xml(self, xml):
        """ Render an XML string into an HTML string.
        """
        if not isinstance(xml, str):
            xml = xml.decode('utf-8')
        return self.render(ET.fromstring(xml))

    def defaultIdScope(self, node):
        """ Default scope for ID attributes when rendering.
        """
        ns = node.nsmap[None]
        scope = node.xpath('./ancestor::a:doc[@name][1]/@name', namespaces={'a': ns})
        if scope:
            return scope[0]


def generate_filename(data, view, format=None):
    if hasattr(data, 'frbr_uri'):
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
    # these are used by the document download menu
    icon = 'far fa-file-code'
    title = 'Akoma Ntoso XML'

    def render(self, data, media_type=None, renderer_context=None):
        if not hasattr(data, 'frbr_uri'):
            return super(AkomaNtosoRenderer, self).render(data, media_type, renderer_context)

        view = renderer_context['view']
        filename = generate_filename(data, view, self.format)
        renderer_context['response']['Content-Disposition'] = 'attachment; filename=%s' % filename

        if not hasattr(view, 'component') or (view.component == 'main' and not view.subcomponent):
            return data.document_xml

        return ET.tostring(view.element, pretty_print=True, encoding='utf-8')


class HTMLRenderer(object):
    """ Render documents as as HTML.
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
            content_html = renderer.render_xml(document.document_xml)

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
        candidates = filename_candidates(document, prefix='xsl/', suffix='.xsl')
        best = find_best_static(candidates)
        if not best:
            raise ValueError("Couldn't find XSLT file to use for %s, tried: %s" % (document, candidates))
        return best

    def _xml_renderer(self, document):
        params = {
            'resolverUrl': self.resolver,
            'mediaUrl': self.media_url or '',
            'lang': document.language.code,
        }

        return XSLTRenderer(xslt_params=params, xslt_filename=self.find_xslt(document))


class HTMLResponseRenderer(StaticHTMLRenderer):
    serializer_class = NoopSerializer

    # these are used by the document download menu
    icon = 'far fa-file-alt'
    title = 'Standalone HTML'
    suffix = '?standalone=1'

    def render(self, document, media_type=None, renderer_context=None):
        if not hasattr(document, 'frbr_uri'):
            return super(HTMLResponseRenderer, self).render(document, media_type, renderer_context)

        view = renderer_context['view']
        renderer = self.get_renderer(renderer_context)

        if not hasattr(view, 'component') or (view.component == 'main' and not view.subcomponent):
            renderer.coverpage = renderer_context['request'].GET.get('coverpage', '1') == '1'
            return renderer.render(document)

        renderer.coverpage = renderer_context['request'].GET.get('coverpage') == '1'
        return renderer.render(document, view.element)

    def get_renderer(self, renderer_context):
        request = renderer_context['request']

        renderer = HTMLRenderer()
        renderer.standalone = request.GET.get('standalone') == '1'
        renderer.resolver = resolver_url(request, request.GET.get('resolver'))
        renderer.media_url = request.GET.get('media-url', '')
        # V2 API responses require that resolvers use /akn as a prefix
        renderer.media_resolver_use_akn_prefix = getattr(request, 'version', None) == 'v2'

        return renderer


class PDFRenderer(HTMLRenderer):
    """ Helper to render documents as PDFs.
    """
    def __init__(self, toc=True, colophon=True, *args, **kwargs):
        super(PDFRenderer, self).__init__(*args, **kwargs)
        self.toc = toc
        self.colophon = colophon

    def render(self, document, element=None):
        self.media_url = 'doc-0/'
        html = super(PDFRenderer, self).render(document, element=element)

        # embed the HTML into the PDF container
        html = render_to_string('indigo_api/akn/export/pdf.html', {
            'documents': [(document, html)],
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            self.save_attachments(html, document, 'doc-0/media/', tmpdir)
            return self.to_pdf(html, tmpdir, document=document)

    def render_many(self, documents, **kwargs):
        html = []

        with tempfile.TemporaryDirectory() as tmpdir:
            # render individual documents
            for i, doc in enumerate(documents):
                self.media_url = f'doc-{i}/'
                doc_html = super(PDFRenderer, self).render(doc, **kwargs)
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
        fnames = set(
            img.get('src')[prefix_len:]
            for img in html.iter('img')
            if img.get('src', '').startswith(prefix)
        )

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

    def to_pdf(self, html, dirname, document=None, documents=None):
        args = []
        options = self.pdf_options()
        options['allow'] = dirname

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

        with tempfile.NamedTemporaryFile(suffix='.html', dir=dirname) as f:
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

        self.book.set_identifier(document.expression_uri.expression_uri())
        self.book.set_title(document.title)
        self.book.set_language(document.language.language.iso)
        self.book.add_author(settings.INDIGO_ORGANISATION)

        self.add_colophon(document)
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

        id = item.id or item.subcomponent
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


class PDFResponseRenderer(BaseRenderer):
    """ Django Rest Framework PDF Renderer.
    """
    media_type = 'application/pdf'
    format = 'pdf'
    serializer_class = NoopSerializer
    pdf_renderer_class = PDFRenderer
    # these are used by the document download menu
    icon = 'far fa-file-pdf'
    title = 'PDF'

    def __init__(self, *args, **kwargs):
        super(PDFResponseRenderer, self).__init__(*args, **kwargs)
        self.cache = caches['default']

    def render(self, data, media_type=None, renderer_context=None):
        if not hasattr(data, 'frbr_uri') and not isinstance(data, list):
            return ''

        view = renderer_context['view']
        filename = self.get_filename(data, view)
        renderer_context['response']['Content-Disposition'] = 'inline; filename=%s' % filename
        request = renderer_context['request']

        renderer = self.get_pdf_renderer()
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
        if hasattr(data, 'frbr_uri'):
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

    def get_pdf_renderer(self):
        return self.pdf_renderer_class()


class EPUBResponseRenderer(PDFResponseRenderer):
    """ Django Rest Framework ePub Renderer.
    """
    media_type = 'application/epub+zip'
    format = 'epub'
    # these are used by the document download menu
    icon = 'fas fa-book'
    title = 'ePUB'

    def render(self, data, media_type=None, renderer_context=None):
        if not hasattr(data, 'frbr_uri') and not isinstance(data, list):
            return ''

        view = renderer_context['view']
        request = renderer_context['request']

        filename = self.get_filename(data, view)
        renderer_context['response']['Content-Disposition'] = 'inline; filename=%s' % filename
        renderer = EPUBRenderer()
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
    # these are used by the document download menu
    icon = 'far fa-file-archive'
    title = 'ZIP Archive'

    def render(self, data, media_type=None, renderer_context=None):
        if not hasattr(data, 'frbr_uri') and not isinstance(data, list):
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
