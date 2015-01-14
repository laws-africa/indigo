from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets

from .models import Document
from .forms import DocumentForm
from .serializers import DocumentSerializer

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
