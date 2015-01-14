from django.shortcuts import render, get_object_or_404

from indigo_api.models import Document
from .forms import DocumentForm

def index(request):
    return render(request, 'index.html')

def document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)
    form = DocumentForm(instance=doc)
    return render(request, 'document/show.html', {
        'document': doc,
        'form': form,
        })
