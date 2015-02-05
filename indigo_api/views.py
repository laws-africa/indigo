from django.template.loader import render_to_string

from rest_framework import viewsets
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from lxml.etree import LxmlError

from .models import Document
from .serializers import DocumentSerializer
from indigo_an.render.html import HTMLRenderer

# REST API
class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

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
