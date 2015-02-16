import re

from django.template.loader import render_to_string

from rest_framework import viewsets
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.views import APIView
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.decorators import detail_route
from lxml.etree import LxmlError

from .models import Document
from .serializers import DocumentSerializer, DocumentBrowserSerializer, AkomaNtosoRenderer
from indigo_an.render.html import HTMLRenderer

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
        if request.method == 'GET':
            return Response({'body_xml': self.get_object().body_xml})

        if request.method == 'PUT':
            instance = self.get_object()

            try:
                instance.body_xml = request.data.get('body_xml')
                instance.save()
            except LxmlError as e:
                raise ValidationError({'body_xml': ["Invalid XML: %s" % e.message]})

            return Response({'body_xml': instance.body_xml})


class FRBRURIViewSet(viewsets.GenericViewSet):
    def initial(self, request, **kwargs):
        super(FRBRURIViewSet, self).initial(request, **kwargs)

        # ensure the URI starts and ends with a slash
        frbr_uri = '/' + self.kwargs['frbr_uri']
        if not frbr_uri.endswith('/'):
            frbr_uri += '/'
        self.kwargs['frbr_uri'] = self.frbr_uri = frbr_uri

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
    serializer_class = DocumentBrowserSerializer
    renderer_classes = (JSONRenderer, AkomaNtosoRenderer, BrowsableAPIRenderer)

    lookup_url_kwarg = 'frbr_uri'
    lookup_field = 'uri'


class PublishedDocumentListView(mixins.ListModelMixin, FRBRURIViewSet):
    """
    The public read-only API for browsing documents by their FRBR URI components.
    """
    queryset = Document.objects.filter(draft=False)
    serializer_class = DocumentBrowserSerializer

    # TODO: don't allow XML serialising here
    # TODO: don't send back document XML in this view

    def filter_queryset(self, queryset):
        return queryset.filter(uri__istartswith=self.frbr_uri)


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
                "body_xml": "... xml ..."
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
            if 'body_xml' in data:
                document.body_xml = data['body_xml']

        elif u'document_xml' in request.data:
            document = Document()
            document.document_xml = request.data['document_xml']
            # TODO: parse the XML to populate the metadata

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
