import lxml.etree as ET
import tempfile
import re

from django.template.loader import find_template, render_to_string, TemplateDoesNotExist
from django.core.cache import get_cache
from rest_framework.renderers import BaseRenderer, StaticHTMLRenderer
from rest_framework_xml.renderers import XMLRenderer
from wkhtmltopdf.utils import make_absolute_paths, wkhtmltopdf

from cobalt.render import HTMLRenderer as CobaltHTMLRenderer
from .serializers import NoopSerializer
from .models import Document


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
    def __init__(self, coverpage=True, template_name=None, cobalt_kwargs=None):
        self.coverpage = coverpage
        self.template_name = template_name
        self.cobalt_kwargs = cobalt_kwargs or {}

    def render(self, document, element=None):
        """ Render this document to HTML.

        :param document: document to render if +element+ is None
        :param element: element to render (optional)
        """
        # use this to render the bulk of the document with the Cobalt XSLT renderer
        renderer = self._xml_renderer(document)
        if element:
            return renderer.render(element)

        content_html = renderer.render_xml(document.document_xml)

        # find the template to use
        template_name = self.template_name or self._find_template(document)

        # and then render some boilerplate around it
        return render_to_string(template_name, {
            'document': document,
            'element': element,
            'content_html': content_html,
            'renderer': renderer,
            'coverpage': self.coverpage,
        })

    def _find_template(self, document):
        """ Return the filename of a template to use to render this document.

        This takes into account the country, type, subtype and language of the document,
        providing a number of opportunities to adjust the rendering logic.
        """
        uri = document.doc.frbr_uri
        doctype = uri.doctype

        options = []
        if uri.subtype:
            options.append('_'.join([doctype, uri.subtype, document.language, uri.country]))
            options.append('_'.join([doctype, uri.subtype, document.language]))
            options.append('_'.join([doctype, uri.subtype, uri.country]))
            options.append('_'.join([doctype, uri.country]))
            options.append('_'.join([doctype, uri.subtype]))

        options.append('_'.join([doctype, document.language, uri.country]))
        options.append('_'.join([doctype, document.language]))
        options.append('_'.join([doctype, uri.country]))
        options.append(doctype)

        options = [f + '.html' for f in options]

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
    def render(self, document, media_type=None, renderer_context=None):
        if not isinstance(document, Document):
            return super(HTMLResponseRenderer, self).render(document, media_type, renderer_context)

        view = renderer_context['view']
        renderer = HTMLRenderer(coverpage=False)

        if view.component == 'main' and not view.subcomponent:
            renderer.coverpage = renderer_context['request'].GET.get('coverpage', 1) == '1'
            return renderer.render(document)

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
        html = render_to_string('pdf/document.html', {
            'document': document,
            'element': element,
            'content_html': html,
        })

        return self.to_pdf(html, document=document)

    def render_many(self, documents, **kwargs):
        html = []

        for doc in documents:
            html.append(super(PDFRenderer, self).render(doc, **kwargs))

        # embed the HTML into the PDF container
        html = render_to_string('pdf/many.html', {
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
        colophon_f = tempfile.NamedTemporaryFile(suffix='.html')
        if False and self.colophon:
            colophon_f.write(self.render_colophon(document=document, documents=documents))
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
        html = render_to_string('pdf/colophon.html', {
            'document': document,
            'documents': documents,
        })
        return make_absolute_paths(html)

    def _wkhtmltopdf(self, *args, **kwargs):
        return wkhtmltopdf(*args, **kwargs)

    def pdf_options(self):
        # see https://eegg.wordpress.com/2010/01/25/page-margins-in-principle-and-practice/ for margin details
        # Target margins are: 36.3mm (top, bottom); 26.6mm (left, right)
        # We want to pull the footer (7.5mm high) into the margin, so we decrease
        # the margin slightly

        footer_spacing = 5
        margin_top = 36.3 - footer_spacing
        margin_bottom = 36.3 - footer_spacing
        margin_left = 26.6

        options = {
            'page-size': 'A4',
            'margin-top': '%.2fmm' % margin_top,
            'margin-bottom': '%2.fmm' % margin_bottom,
            'margin-left': '%.2fmm' % margin_left,
            'margin-right': '%.2fmm' % margin_left,
            'footer-right': '[page]/[toPage]',
            'footer-spacing': '%.2f' % footer_spacing,
            'footer-font-name': 'Georgia, Times New Roman',
            'footer-font-size': '10',
            'xsl-style-sheet': find_template('pdf/toc.xsl')[0].origin.name,
        }

        return options


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

        return parts

    def get_filename(self, data, view):
        if isinstance(data, Document):
            parts = [data.year, data.number]
            if hasattr(view, 'component'):
                parts.extend([view.component if view.component != 'main' else None, view.subcomponent])
        else:
            parts = view.kwargs['frbr_uri'].split('/')

        parts = [re.sub('[/ .]', '-', p) for p in parts if p]

        return '-'.join(parts) + '.pdf'
