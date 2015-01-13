from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets

from .models import Document
from .serializers import DocumentSerializer

def index(request):
    return render(request, 'index.html')

def document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)
    return render(request, 'document/show.html', {
        'document': doc,
        })
    
# REST API
class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
