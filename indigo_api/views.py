import re
import logging

from django.template.loader import render_to_string
from django.http import Http404

from rest_framework import viewsets
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.views import APIView
from rest_framework import mixins, viewsets, renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from lxml.etree import LxmlError
import arrow

from .models import Document
from .serializers import DocumentSerializer, AkomaNtosoRenderer, ConvertSerializer
from .importer import Importer
from indigo_an.render.html import HTMLRenderer

log = logging.getLogger(__name__)

FORMAT_RE = re.compile('\.([a-z0-9]+)$')

# REST API
class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Document.objects.filter(deleted__exact=False).all()
    serializer_class = DocumentSerializer

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()

    @detail_route(methods=['GET', 'PUT'])
    def body(self, request, *args, **kwargs):
        """ This exposes a GET and PUT resource at ``/api/documents/1/body`` which allows
        the body of the document to be fetched and set independently of the metadata. This
        is useful because the body can be large.
        """
        instance = self.get_object()

        if request.method == 'GET':
            return Response({'body': instance.body})

        if request.method == 'PUT':
            try:
                instance.body = request.data.get('body')
                instance.save()
            except LxmlError as e:
                raise ValidationError({'body': ["Invalid XML: %s" % e.message]})

            return Response({'body': instance.body})

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
        instance = self.get_object()
        return Response({'toc': self.get_object().table_of_contents()})


class FRBRURIViewSet(viewsets.GenericViewSet):
    def initial(self, request, **kwargs):
        super(FRBRURIViewSet, self).initial(request, **kwargs)

        # ensure the URI starts and ends with a slash
        frbr_uri = '/' + self.kwargs['frbr_uri']
        if not frbr_uri.endswith('/'):
            frbr_uri += '/'
        self.kwargs['frbr_uri'] = frbr_uri

    def get_format_suffix(self, **kwargs):
        match = FORMAT_RE.search(self.kwargs['frbr_uri'])
        if match:
            # strip it from the uri
            self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][0:match.start()]
            return match.group(1)


class PublishedDocumentDetailView(mixins.RetrieveModelMixin, FRBRURIViewSet):
    """
    The public read-only API for viewing a document by FRBR URI.
    """
    queryset = Document.objects.filter(draft=False)
    serializer_class = DocumentSerializer
    # these determine what content negotiation takes place
    renderer_classes = (renderers.JSONRenderer, AkomaNtosoRenderer, renderers.StaticHTMLRenderer)

    lookup_url_kwarg = 'frbr_uri'
    lookup_field = 'frbr_uri'

    def retrieve(self, request, *args, **kwargs):
        component = self.get_component()
        format = self.request.accepted_renderer.format

        # get the document
        document = self.get_object()

        if (component, format) == ('main', 'xml'):
            return Response(document.document_xml)

        if (component, format) == ('main', 'html'):
            html = HTMLRenderer().render_xml(document.document_xml)
            return Response(html)

        # table of content
        if (component, format) == ('toc', 'json'):
            serializer = self.get_serializer(document)
            return Response({'toc': document.table_of_contents()})

        if (component, format) == ('main', 'json'):
            serializer = self.get_serializer(document)
            return Response(serializer.data)

        raise Http404

    def get_component(self):
        # split the URI into the base, and the component
        #
        # /za/act/1998/84/main -> (/za/act/1998/84/, main)

        parts = self.kwargs['frbr_uri'].split('/')
        self.kwargs['frbr_uri'] = '/'.join(parts[0:5]) + '/'

        component = '/'.join(parts[5:]) or 'main'
        if component.endswith('/'):
            component = component[0:-1]

        return component



class PublishedDocumentListView(mixins.ListModelMixin, FRBRURIViewSet):
    """
    The public read-only API for browsing documents by their FRBR URI components.
    """
    queryset = Document.objects.filter(draft=False)
    serializer_class = DocumentSerializer

    def filter_queryset(self, queryset):
        queryset = queryset.filter(frbr_uri__istartswith=self.kwargs['frbr_uri'])
        if queryset.count() == 0:
            raise Http404
        return queryset


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
                document = Document(**doc_serializer.validated_data)

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
            document_xml: "xml" (optional)
            document: { ... } (optional)

        To determine what to render, include either a full document description or a `document_xml` value.

            {
              "document": {
                "title": "A title",
                "body": "... xml ..."
              }
            }

            OR

            {
              "document_xml": "... xml ..."
            }
        """

        if u'document' in request.data:
            data = request.data['document']
            # try to load the document data
            if 'id' in data:
                document = Document.objects.filter(id=data['id']).first()
            else:
                document = Document()

            # update the model from the db
            ds = DocumentSerializer(instance=document, data=data)
            if ds.is_valid(raise_exception=True):
                ds.update(document, ds.validated_data)

            # patch in the body xml
            if 'body' in data:
                document.body = data['body']

        elif u'content' in request.data:
            document = Document()
            document.content = request.data['content']

        else:
            raise ParseError("Provide either a 'document' or 'document_xml' item.")

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
