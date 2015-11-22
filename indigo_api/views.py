import re
import logging

from django.http import Http404, HttpResponse
from django.views.decorators.cache import cache_control

from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework import mixins, viewsets, renderers
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, AllowAny
import reversion

import lxml.html.diff
from lxml.etree import LxmlError

from .models import Document, Attachment
from .serializers import DocumentSerializer, ConvertSerializer, AttachmentSerializer, LinkTermsSerializer, RevisionSerializer
from .renderers import AkomaNtosoRenderer, PDFResponseRenderer, HTMLResponseRenderer
from .atom import AtomRenderer, AtomFeed
from .slaw import Importer, Slaw
from .authz import DocumentPermissions
from cobalt import FrbrUri
from cobalt.render import HTMLRenderer
import newrelic.agent

log = logging.getLogger(__name__)

FORMAT_RE = re.compile('\.([a-z0-9]+)$')


def ping(request):
    newrelic.agent.ignore_transaction()
    return HttpResponse("pong", content_type="text/plain")


def view_attachment(attachment):
    response = HttpResponse(attachment.file.read(), content_type=attachment.mime_type)
    response['Content-Disposition'] = 'inline; filename=%s' % attachment.filename
    response['Content-Length'] = str(attachment.size)
    return response


def download_attachment(attachment):
    response = view_attachment(attachment)
    response['Content-Disposition'] = 'attachment; filename=%s' % attachment.filename
    return response


class DocumentViewMixin(object):
    queryset = Document.objects.undeleted().prefetch_related('tags', 'created_by_user', 'updated_by_user')

    def initial(self, request, **kwargs):
        super(DocumentViewMixin, self).initial(request, **kwargs)

        # some of our renderers want to bypass the serializer, so that we get access to the
        # raw data objects
        if getattr(self.request.accepted_renderer, 'serializer_class', None):
            self.serializer_class = self.request.accepted_renderer.serializer_class

    def table_of_contents(self, document):
        # this updates the TOC entries by adding a 'url' component
        # based on the document's URI and the path of the TOC subcomponent
        uri = document.doc.frbr_uri
        toc = document.table_of_contents()

        def add_url(item):
            uri.expression_component = item['component']
            uri.expression_subcomponent = item.get('subcomponent')

            item['url'] = reverse(
                'published-document-detail',
                request=self.request,
                kwargs={'frbr_uri': uri.expression_uri()[1:]})

            for kid in item.get('children', []):
                add_url(kid)

        for item in toc:
            add_url(item)

        return toc


# Read/write REST API
class DocumentViewSet(DocumentViewMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    serializer_class = DocumentSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly, DocumentPermissions)
    renderer_classes = (renderers.JSONRenderer, PDFResponseRenderer, HTMLResponseRenderer, renderers.BrowsableAPIRenderer)

    def perform_destroy(self, instance):
        if not instance.draft:
            raise MethodNotAllowed('DELETE', 'DELETE not allowed for published documents, mark as draft first.')
        instance.deleted = True
        instance.save()

    def perform_update(self, serializer):
        # check permissions just before saving, to prevent users
        # without publish permissions from setting draft = False
        if not DocumentPermissions().update_allowed(self.request, serializer):
            self.permission_denied(self.request)

        super(DocumentViewSet, self).perform_update(serializer)

    @detail_route(methods=['GET', 'PUT'])
    def content(self, request, *args, **kwargs):
        """ This exposes a GET and PUT resource at ``/api/documents/1/content`` which allows
        the content of the document to be fetched and set independently of the metadata. This
        is useful because the content can be large.
        """
        instance = self.get_object()

        if request.method == 'GET':
            return Response({'content': self.get_object().document_xml})

        if request.method == 'PUT':
            try:
                instance.reset_xml(request.data.get('content'))
                instance.save()
            except LxmlError as e:
                raise ValidationError({'content': ["Invalid XML: %s" % e.message]})

            return Response({'content': instance.document_xml})

    @detail_route(methods=['GET'])
    def toc(self, request, *args, **kwargs):
        """ This exposes a GET resource at ``/api/documents/1/toc`` which gives
        a table of contents for the document.
        """
        return Response({'toc': self.table_of_contents(self.get_object())})


class DocumentResourceView(object):
    """ Helper mixin for views that hang off of a document URL. """
    def initial(self, request, **kwargs):
        self.document = self.lookup_document()
        super(DocumentResourceView, self).initial(request, **kwargs)

    def lookup_document(self):
        qs = Document.objects.defer('document_xml')
        doc_id = self.kwargs['document_id']
        return get_object_or_404(qs, deleted__exact=False, id=doc_id)

    def get_serializer_context(self):
        context = super(DocumentResourceView, self).get_serializer_context()
        context['document'] = self.document
        return context


class AttachmentViewSet(DocumentResourceView, viewsets.ModelViewSet):
    queryset = Attachment.objects
    serializer_class = AttachmentSerializer

    @detail_route(methods=['GET'])
    def download(self, request, *args, **kwargs):
        attachment = self.get_object()
        return download_attachment(attachment)

    @detail_route(methods=['GET'])
    def view(self, request, *args, **kwargs):
        attachment = self.get_object()
        return view_attachment(attachment)

    def filter_queryset(self, queryset):
        return queryset.filter(document=self.document).all()


class RevisionViewSet(DocumentResourceView, viewsets.ReadOnlyModelViewSet):
    serializer_class = RevisionSerializer

    @detail_route(methods=['POST'])
    def restore(self, request, *args, **kwargs):
        # check permissions on the OLD object
        if not DocumentPermissions().has_object_permission(request, self, self.document):
            self.permission_denied(self.request)

        revision = self.get_object()

        # check permissions on the NEW object
        version = revision.version_set.all()[0]
        document = version.object_version.object
        if not DocumentPermissions().has_object_permission(request, self, document):
            self.permission_denied(self.request)

        with reversion.create_revision():
            reversion.set_user(request.user)
            reversion.set_comment("Restored revision %s" % revision.id)
            revision.revert()

        return Response(status=200)

    @detail_route(methods=['GET'])
    @cache_control(public=True, max_age=24 * 3600)
    def diff(self, request, *args, **kwargs):
        # this can be cached because the underlying data won't change (although
        # the formatting might)
        revision = self.get_object()
        version = revision.version_set.all()[0]

        # most recent version just before this one
        old_version = reversion.models.Version.objects\
            .filter(content_type=version.content_type)\
            .filter(object_id_int=version.object_id_int)\
            .filter(id__lt=version.id)\
            .order_by('-id')\
            .first()

        if old_version:
            old_html = old_version.object_version.object.to_html()
        else:
            old_html = ""
        new_html = version.object_version.object.to_html()
        diff = lxml.html.diff.htmldiff(old_html, new_html)

        # TODO: include other diff'd attributes

        return Response({'content': diff})

    def get_queryset(self):
        return self.document.revisions()


class PublishedDocumentDetailView(DocumentViewMixin,
                                  mixins.RetrieveModelMixin,
                                  mixins.ListModelMixin,
                                  viewsets.GenericViewSet):
    """
    The public read-only API for viewing and listing published documents by FRBR URI.

    This handles both listing many documents based on a URI prefix, and
    returning details for a single document. The default content type
    is JSON.

    For example:

    * ``/za/``: list all published documents for South Africa.
    * ``/za/act/1994/2/``: one document, Act 2 of 1992
    * ``/za/act/1994/summary.atom``: all the acts from 1994 as an atom feed
    * ``/za/act/1994.pdf``: all the acts from 1994 as a PDF

    """
    queryset = DocumentViewMixin.queryset.published().order_by('id')

    serializer_class = DocumentSerializer
    pagination_class = PageNumberPagination
    # these determine what content negotiation takes place
    renderer_classes = (renderers.JSONRenderer, AtomRenderer, PDFResponseRenderer, AkomaNtosoRenderer, HTMLResponseRenderer)

    def initial(self, request, **kwargs):
        super(PublishedDocumentDetailView, self).initial(request, **kwargs)
        # ensure the URI starts with a slash
        self.kwargs['frbr_uri'] = '/' + self.kwargs['frbr_uri']

    def get(self, request, **kwargs):
        # try parse it as an FRBR URI, if that succeeds, we'll lookup the document
        # that document matches, otherwise we'll assume they're trying to
        # list documents with a prefix URI match.
        try:
            self.frbr_uri = FrbrUri.parse(self.kwargs['frbr_uri'])

            # ensure we haven't mistaken '/za-cpt/act/by-law/2011/full.atom' for a URI
            if self.frbr_uri.number in ['full', 'summary'] and self.format_kwarg == 'atom':
                raise ValueError()

            # in a URL like
            #
            #   /act/1980/1/toc
            #
            # don't mistake 'toc' for a language, it's really equivalent to
            #
            #   /act/1980/1/eng/toc
            #
            # if eng is the default language.
            if self.frbr_uri.language == 'toc':
                self.frbr_uri.language = self.frbr_uri.default_language
                self.frbr_uri.expression_component = 'toc'

            return self.retrieve(request)
        except ValueError:
            return self.list(request)

    def retrieve(self, request, *args, **kwargs):
        """ Return details on a single document, possible only part of that document.
        """
        # these are made available to the renderer
        self.component = self.frbr_uri.expression_component or 'main'
        self.subcomponent = self.frbr_uri.expression_subcomponent
        format = self.request.accepted_renderer.format
        # Tell the renderer that published documents shouldn't include stub content
        self.no_stub_content = True

        # get the document
        document = self.get_object()

        if self.subcomponent:
            self.element = document.doc.get_subcomponent(self.component, self.subcomponent)
        else:
            # special cases of the entire document

            # table of contents
            if (self.component, format) == ('toc', 'json'):
                return Response({'toc': self.table_of_contents(document)})

            # json description
            if (self.component, format) == ('main', 'json'):
                serializer = self.get_serializer(document)
                return Response(serializer.data)

            # the item we're interested in
            self.element = document.doc.components().get(self.component)

        if self.element and format in ['xml', 'html', 'pdf']:
            return Response(document)

        raise Http404

    def list(self, request):
        """ Return details on many documents.
        """
        if self.request.accepted_renderer.format == 'atom':
            # feeds show most recently changed first
            self.queryset = self.queryset.order_by('-updated_at')

            # what type of feed?
            if self.kwargs['frbr_uri'].endswith('summary'):
                self.kwargs['feed'] = 'summary'
                self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][:-7]
            elif self.kwargs['frbr_uri'].endswith('full'):
                self.kwargs['feed'] = 'full'
                self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][:-4]
            else:
                raise Http404

            if self.kwargs['feed'] == 'full':
                # full feed is big, limit it
                self.paginator.page_size = AtomFeed.full_feed_page_size

        elif self.request.accepted_renderer.format == 'pdf':
            # TODO: ordering?
            documents = list(self.filter_queryset(self.get_queryset()).all())
            # bypass pagination and serialization
            return Response(documents)

        elif self.format_kwarg and self.format_kwarg != "json":
            # they explicitly asked for something other than JSON,
            # but listing views don't support that, so 404
            raise Http404

        else:
            # either explicitly or implicitly json
            self.request.accepted_renderer = renderers.JSONRenderer()
            self.request.accepted_media_type = self.request.accepted_renderer.media_type
            self.serializer_class = PublishedDocumentDetailView.serializer_class

        response = super(PublishedDocumentDetailView, self).list(request)

        # add alternate links for json
        if self.request.accepted_renderer.format == 'json':
            self.add_alternate_links(response, request)

        return response

    def add_alternate_links(self, response, request):
        url = reverse('published-document-detail', request=request,
                      kwargs={'frbr_uri': self.kwargs['frbr_uri'][1:]})

        if url.endswith('/'):
            url = url[:-1]

        response.data['links'] = [
            {
                "rel": "alternate",
                "title": AtomFeed.summary_feed_title,
                "href": url + "/summary.atom",
                "mediaType": AtomRenderer.media_type,
            },
            {
                "rel": "alternate",
                "title": AtomFeed.full_feed_title,
                "href": url + "/full.atom",
                "mediaType": AtomRenderer.media_type,
            },
            {
                "rel": "alternate",
                "title": "PDF",
                "href": url + ".pdf",
                "mediaType": "application/pdf"
            },
        ]

    def get_object(self):
        """ Find and return one document, used by retrieve()
        """
        try:
            obj = self.get_queryset().get_for_frbr_uri(self.frbr_uri)
            if not obj:
                raise ValueError()
        except ValueError as e:
            raise Http404(e.message)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def filter_queryset(self, queryset):
        """ Filter the queryset, used by list()
        """
        queryset = queryset.filter(frbr_uri__istartswith=self.kwargs['frbr_uri'])
        if queryset.count() == 0:
            raise Http404
        return queryset

    def get_format_suffix(self, **kwargs):
        """ Used during content negotiation.
        """
        match = FORMAT_RE.search(self.kwargs['frbr_uri'])
        if match:
            # strip it from the uri
            self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][0:match.start()]
            return match.group(1)

    def handle_exception(self, exc):
        # Formats like atom and XML don't render exceptions well, so just
        # fall back to HTML
        if hasattr(self.request, 'accepted_renderer') and self.request.accepted_renderer.format in ['xml', 'atom']:
            self.request.accepted_renderer = renderers.StaticHTMLRenderer()
            self.request.accepted_media_type = renderers.StaticHTMLRenderer.media_type

        return super(PublishedDocumentDetailView, self).handle_exception(exc)


class ConvertView(APIView):
    """
    Support for converting between two document types. This allows conversion from
    plain text, JSON, XML, and PDF to plain text, JSON, XML and HTML.
    """

    # Allow anyone to use this API, it uses POST but doesn't change
    # any documents in the database and so is safe.
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        serializer, document = self.handle_input()
        output_format = serializer.validated_data.get('outputformat')
        return self.handle_output(document, output_format)

    def handle_input(self):
        self.fragment = self.request.data.get('fragment')
        document = None
        serializer = ConvertSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        input_format = serializer.validated_data.get('inputformat')

        upload = self.request.data.get('file')
        if upload:
            # we got a file
            try:
                document = self.get_importer().import_from_upload(upload)
                return serializer, document
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'file': e.message or "error during import"})

        elif input_format == 'application/json':
            doc_serializer = DocumentSerializer(
                data=self.request.data['content'],
                context={'request': self.request})
            doc_serializer.is_valid(raise_exception=True)
            document = doc_serializer.update_document(Document())

        elif input_format == 'text/plain':
            try:
                document = self.get_importer().import_from_text(self.request.data['content'])
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'content': e.message or "error during import"})

        if not document:
            raise ValidationError("Nothing to convert! Either 'file' or 'content' must be provided.")

        return serializer, document

    def handle_output(self, document, output_format):
        if output_format == 'application/json':
            if self.fragment:
                raise ValidationError("Cannot output application/json from a fragment")

            # disable tags, they can't be used without committing this object to the db
            document.tags = None

            doc_serializer = DocumentSerializer(instance=document, context={'request': self.request})
            data = doc_serializer.data
            data['content'] = document.document_xml.decode('utf-8')
            return Response(data)

        if output_format == 'application/xml':
            if self.fragment:
                return Response({'output': document.to_xml()})
            else:
                return Response({'output': document.document_xml})

        if output_format == 'text/html':
            if self.fragment:
                # TODO: use document.to_html
                return Response(HTMLRenderer().render(document.to_xml()))
            else:
                return Response({'output': document.to_html()})

        # TODO: handle plain text output

    def get_importer(self):
        importer = Importer()
        importer.fragment = self.request.data.get('fragment')
        importer.fragment_id_prefix = self.request.data.get('id_prefix')

        return importer


class LinkTermsView(APIView):
    """
    Support for running term discovery and linking on a document.
    """

    # Allow anyone to use this API, it uses POST but doesn't change
    # any documents in the database and so is safe.
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = LinkTermsSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        doc_serializer = DocumentSerializer(
            data=self.request.data['document'],
            context={'request': self.request})
        doc_serializer.is_valid(raise_exception=True)
        if not doc_serializer.validated_data.get('content'):
            raise ValidationError({'document': ["Content cannot be empty."]})

        document = doc_serializer.update_document(Document())
        self.link_terms(document)

        return Response({'document': {'content': document.document_xml}})

    def link_terms(self, doc):
        Slaw().link_terms(doc)
