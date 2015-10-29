import lxml.etree as ET
import tempfile
import re
import os.path

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
    def __init__(self, coverpage=True, standalone=False, template_name=None, cobalt_kwargs=None):
        self.template_name = template_name
        self.standalone = standalone
        self.cobalt_kwargs = cobalt_kwargs or {}
        self.coverpage = coverpage

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
        elif document.stub:
            # Stub
            content_html = ''
        else:
            # the entire document
            content_html = renderer.render_xml(document.document_xml)

        # find the template to use
        template_name = self.template_name or self._find_template(document)

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
            context['colophon'] = self._find_colophon_template(document)
            return render_to_string('export/standalone.html', context)
        else:
            return render_to_string(template_name, context)

    def _find_colophon_template(self, document):
        try:
            return self._find_template(document, 'export/colophon_')
        except ValueError:
            return None

    def _find_template(self, document, prefix=''):
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
        template = self._find_colophon_template(document or documents[0])
        if template:
            return make_absolute_paths(render_to_string(template))

    def _wkhtmltopdf(self, *args, **kwargs):
        return wkhtmltopdf(*args, **kwargs)

    def pdf_options(self):
        # see https://eegg.wordpress.com/2010/01/25/page-margins-in-principle-and-practice/ for margin details
        # Target margins are: 36.3mm (top, bottom); 26.6mm (left, right)
        # We want to pull the footer (7.5mm high) into the margin, so we decrease
        # the margin slightly

        footer_font = 'Georgia, "Times New Roman", serif'
        footer_font_size = '10'
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
