import re
import logging

from django.template.loader import render_to_string
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework import mixins, viewsets, renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route
import lxml.etree as ET
from lxml.etree import LxmlError

from .models import Document
from .serializers import DocumentSerializer, AkomaNtosoRenderer, ConvertSerializer
from .importer import Importer
from cobalt import FrbrUri
from cobalt.render import HTMLRenderer

log = logging.getLogger(__name__)

FORMAT_RE = re.compile('\.([a-z0-9]+)$')


class DocumentViewMixin(object):
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


# REST API
class DocumentViewSet(DocumentViewMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Document.objects.filter(deleted__exact=False).all()
    serializer_class = DocumentSerializer

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()

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


class PublishedDocumentDetailView(DocumentViewMixin,
                                  mixins.RetrieveModelMixin,
                                  mixins.ListModelMixin,
                                  viewsets.GenericViewSet):
    """
    The public read-only API for viewing and listing documents by FRBR URI.
    """
    queryset = Document.objects.filter(draft=False)
    serializer_class = DocumentSerializer
    # these determine what content negotiation takes place
    renderer_classes = (renderers.JSONRenderer, AkomaNtosoRenderer, renderers.StaticHTMLRenderer)

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

    def list(self, request):
        # force JSON for list view
        self.request.accepted_renderer = renderers.JSONRenderer()
        self.request.accepted_media_type = self.request.accepted_renderer.media_type
        return super(PublishedDocumentDetailView, self).list(request)

    def retrieve(self, request, *args, **kwargs):
        component = self.frbr_uri.expression_component or 'main'
        subcomponent = self.frbr_uri.expression_subcomponent
        format = self.request.accepted_renderer.format

        # get the document
        document = self.get_object()

        if subcomponent:
            element = document.doc.get_subcomponent(component, subcomponent)

        else:
            # special cases of the entire document

            # table of contents
            if (component, format) == ('toc', 'json'):
                serializer = self.get_serializer(document)
                return Response({'toc': self.table_of_contents(document)})

            # json description
            if (component, format) == ('main', 'json'):
                serializer = self.get_serializer(document)
                return Response(serializer.data)

            # entire thing
            if (component, format) == ('main', 'xml'):
                return Response(document.document_xml)

            # the item we're interested in
            element = document.doc.components().get(component)

        if element:
            if format == 'html':
                return Response(HTMLRenderer().render(element))

            if format == 'xml':
                return Response(ET.tostring(element, pretty_print=True))

        raise Http404

    def get_object(self):
        """ Filter one document,  used by retrieve() """
        # TODO: filter on expression (expression date, etc.)
        # TODO: support multiple docs
        obj = get_object_or_404(self.get_queryset().filter(frbr_uri=self.frbr_uri.work_uri()))

        if obj.language != self.frbr_uri.language:
            raise Http404("The document %s exists but is not available in the language '%s'"
                          % (self.frbr_uri.work_uri(), self.frbr_uri.language))

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def filter_queryset(self, queryset):
        """ Filter the queryset, used by list() """
        queryset = queryset.filter(frbr_uri__istartswith=self.kwargs['frbr_uri'])
        if queryset.count() == 0:
            raise Http404
        return queryset

    def get_format_suffix(self, **kwargs):
        # we could also pull this from the parsed URI
        match = FORMAT_RE.search(self.kwargs['frbr_uri'])
        if match:
            # strip it from the uri
            self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][0:match.start()]
            return match.group(1)


class ConvertView(APIView):
    """
    Support for converting between two document types. This allows conversion from
    plain text, JSON, XML, and PDF to plain text, JSON, XML and HTML.
    """

    def post(self, request, format=None):
        serializer, document = self.handle_input()
        output_format = serializer.validated_data.get('outputformat')
        return self.handle_output(document, output_format)

    def handle_input(self):
        document = None
        serializer = ConvertSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        upload = self.request.data.get('file')
        if upload:
            # we got a file
            try:
                document = Importer().import_from_upload(upload)
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'file': e.message or "error during import"})

        else:
            # handle non-file inputs
            input_format = serializer.validated_data.get('inputformat')
            if input_format == 'json':
                doc_serializer = DocumentSerializer(
                    data=self.request.data['content'],
                    context={'request': self.request})
                doc_serializer.is_valid(raise_exception=True)
                document = doc_serializer.update_document(Document())

        if not document:
            raise ValidationError("Nothing to convert! Either 'file' or 'content' must be provided.")

        return serializer, document

    def handle_output(self, document, output_format):
        if output_format == 'json':
            doc_serializer = DocumentSerializer(instance=document, context={'request': self.request})
            data = doc_serializer.data
            data['content'] = document.document_xml
            return Response(data)

        if output_format == 'xml':
            return Response(document.document_xml)

        if output_format == 'html':
            renderer = HTMLRenderer()
            body_html = renderer.render_xml(document.document_xml)
            return Response(body_html)

        # TODO: handle plain text output


class RenderAPI(APIView):
    def post(self, request, format=None):
        """
        Render a document into HTML. The request MUST include a JSON description of
        what to render.

        Parameters:

            format: "html" (default)
            document: { ... }

        To determine what to render, include a document description. If the description has an
        id, the missing details are filled in from the existing document in the database.

            {
              "document": {
                "title": "A title",
                "content": "... xml ..."
              }
            }
        """

        if u'document' in request.data:
            data = request.data['document']
            # try to load the document data
            if 'id' in data:
                document = Document.objects.filter(id=data['id']).first()
            else:
                document = Document()

            # update the model, but don't save it
            ds = DocumentSerializer(instance=document, data=data)
            if ds.is_valid(raise_exception=True):
                ds.update_document(document)

        else:
            raise ParseError("Required parameter 'document' is missing.")

        if not document.document_xml:
            html = ""
        else:
            renderer = HTMLRenderer()
            body_html = renderer.render_xml(document.document_xml)

            html = render_to_string('html_preview.html', {
                'document': document,
                'body_html': body_html,
            })

        return Response({'html': html})
