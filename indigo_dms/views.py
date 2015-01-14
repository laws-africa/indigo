from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Document
from .forms import DocumentForm
from .serializers import DocumentSerializer
from .an.render.html import HTMLRenderer

def index(request):
    return render(request, 'index.html')

def document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)
    form = DocumentForm(instance=doc)
    return render(request, 'document/show.html', {
        'document': doc,
        'form': form,
        })
    
# REST API
class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

class RenderAPI(APIView):
    def post(self, request, format=None):
        """
        Render a document into HTML. The request MUST include a JSON description of
        what to render.

        Parameters:

            format: "html" (default)
            content_xml: "xml" (optional)
            document: { ... } (optional)

        To determine what to render, include either a full document description or a `content_xml` value.

            {
              "document": {
                "title": "A title",
                "content_xml": "... xml ..."
              }
            }

            OR

            {
              "content_xml": "... xml ..."
            }
        """

        if u'document' in request.data:
            # get document description
            # TODO:
            pass

        elif u'content_xml' in request.data:
            xml = request.data['content_xml']

        else:
            raise ParseError("Provide either a 'document' or 'content_xml' item.")

        if not xml:
            html = ""
        else:
            renderer = HTMLRenderer()
            html = renderer.render_xml(xml)

        return Response({'html': html})
