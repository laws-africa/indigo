import lxml.etree as ET
import tempfile
import re
import zipfile
import logging

from django.core.cache import caches
from django.conf import settings
from rest_framework.renderers import BaseRenderer, StaticHTMLRenderer
from rest_framework_xml.renderers import XMLRenderer

from indigo.plugins import plugins
from indigo_api.exporters import HTMLExporter, PDFExporter, EPUBExporter
from .serializers import NoopSerializer

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


class ExporterMixin:
    """ Mixin for Indigo response renderers to make subclassing simpler.
    """
    exporter_class = None

    def get_exporter(self, *args, **kwargs):
        return self.exporter_class(*args, **kwargs)


def generate_filename(data, view, format=None):
    if hasattr(data, 'frbr_uri'):
        parts = [data.year, data.number]
        if hasattr(view, 'component'):
            parts.extend([view.component if view.component != 'main' else None, view.portion])
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

        if not hasattr(view, 'component') or (view.component == 'main' and not view.portion):
            return data.document_xml

        return ET.tostring(view.element, pretty_print=True, encoding='utf-8')


class HTMLRenderer(StaticHTMLRenderer, ExporterMixin):
    serializer_class = NoopSerializer
    exporter_class = HTMLExporter

    # these are used by the document download menu
    icon = 'far fa-file-alt'
    title = 'Standalone HTML'
    suffix = '?standalone=1'

    def render(self, document, media_type=None, renderer_context=None):
        self.renderer_context = renderer_context

        if not hasattr(document, 'frbr_uri'):
            return super(HTMLRenderer, self).render(document, media_type, renderer_context)

        view = renderer_context['view']
        exporter = self.get_exporter()

        if not hasattr(view, 'component') or (view.component == 'main' and not view.portion):
            exporter.coverpage = renderer_context['request'].GET.get('coverpage', '1') == '1'
            return exporter.render(document)

        exporter.coverpage = renderer_context['request'].GET.get('coverpage') == '1'
        return exporter.render(document, view.element)

    def get_exporter(self):
        request = self.renderer_context['request']

        exporter = super().get_exporter()
        exporter.standalone = request.GET.get('standalone') == '1'
        exporter.resolver = resolver_url(request, request.GET.get('resolver'))
        exporter.media_url = request.GET.get('media-url', '')
        # V2 API responses require that resolvers use /akn as a prefix
        exporter.media_resolver_use_akn_prefix = getattr(request, 'version', None) == 'v2'

        return exporter


class PDFRenderer(BaseRenderer):
    """ Django Rest Framework PDF Renderer.
    """
    media_type = 'application/pdf'
    format = 'pdf'
    serializer_class = NoopSerializer
    renderer_context = None

    # these are used by the document download menu
    icon = 'far fa-file-pdf'
    title = 'PDF'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = caches['default']

    def render(self, data, media_type=None, renderer_context=None):
        self.renderer_context = renderer_context

        # we don't support rendering more than one PDF
        if not hasattr(data, 'frbr_uri') or isinstance(data, list):
            return ''

        view = renderer_context['view']

        # check the cache
        key = self.cache_key(data, view)
        if key:
            pdf = self.cache.get(key)
            if pdf:
                return pdf

        filename = self.get_filename(data, view)
        renderer_context['response']['Content-Disposition'] = 'inline; filename=%s' % filename
        request = renderer_context['request']
        exporter = self.get_exporter()
        exporter.resolver = resolver_url(request, request.GET.get('resolver'))

        if not hasattr(view, 'component') or (view.component == 'main' and not view.portion):
            # whole document
            pdf = exporter.render(data)
        else:
            # we don't support rendering partial PDFs
            return ''

        # cache it
        if key:
            self.cache.set(key, pdf)

        return pdf

    def get_exporter(self, *args, **kwargs):
        return plugins.for_locale('pdf-exporter')

    def cache_key(self, data, view):
        if hasattr(data, 'frbr_uri'):
            # it's unsaved, don't bother
            if data.id is None:
                return None

            parts = [str(data.id), data.updated_at.isoformat()]
            if hasattr(view, 'component'):
                parts.append(view.component)
                parts.append(view.portion)
        else:
            # list of docs
            data = sorted(data, key=lambda d: d.id)
            parts = [f"{p.id}-{p.updated_at.isoformat()}" for p in data]

        parts = [self.format] + parts
        return ':'.join(str(p) for p in parts)

    def get_filename(self, data, view):
        return generate_filename(data, view, self.format)


class EPUBRenderer(ExporterMixin, PDFRenderer):
    """ Django Rest Framework ePub Renderer.
    """
    media_type = 'application/epub+zip'
    format = 'epub'
    exporter_class = EPUBExporter

    # these are used by the document download menu
    icon = 'fas fa-book'
    title = 'ePUB'

    def render(self, data, media_type=None, renderer_context=None):
        self.renderer_context = renderer_context

        if not hasattr(data, 'frbr_uri') and not isinstance(data, list):
            return ''

        view = renderer_context['view']
        request = renderer_context['request']

        filename = self.get_filename(data, view)
        renderer_context['response']['Content-Disposition'] = 'inline; filename=%s' % filename
        exporter = self.get_exporter()
        exporter.resolver = resolver_url(request, request.GET.get('resolver'))

        # check the cache
        key = self.cache_key(data, view)
        if key:
            epub = self.cache.get(key)
            if epub:
                return epub

        if isinstance(data, list):
            # render many
            epub = exporter.render_many(data)
        elif not hasattr(view, 'component') or (view.component == 'main' and not view.portion):
            # whole document
            epub = exporter.render(data)
        else:
            # just one element
            exporter.toc = False
            epub = exporter.render(data, view.element)

        # cache it
        if key:
            self.cache.set(key, epub)

        return epub


class ZIPRenderer(BaseRenderer):
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
        self.renderer_context = renderer_context

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
                self.add_attachments(document, zf, prefix)

    def add_attachments(self, document, zf, prefix):
        for attachment in document.attachments.all():
            zf.writestr(prefix + "media/" + attachment.filename, attachment.file.read())
