from django.shortcuts import render, get_object_or_404

from .models import Document

def index(request):
    return render(request, 'index.html')

def document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)
    return render(request, 'document/show.html', {
        'doc': doc,
        })
    
