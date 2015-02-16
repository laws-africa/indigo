from django.shortcuts import render, get_object_or_404
from django.views.generic.base import TemplateView

from indigo_api.models import Document
from .forms import DocumentForm

def document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)
    form = DocumentForm(instance=doc)
    return render(request, 'document/show.html', {
        'document': doc,
        'form': form,
        'view': 'DocumentView',
        })

def new_document(request):
    doc = Document(title='(untitled)')
    form = DocumentForm(instance=doc)
    return render(request, 'document/show.html', {
        'document': doc,
        'form': form,
        'view': 'DocumentView',
        })

def library(request):
    return render(request, 'library.html', {
        'view': 'LibraryView',
        })

def password_reset_confirm(request, uidb64, token):
    return render(request, 'user/password_reset_confirm.html', {
        'uid': uidb64,
        'token': token,
        })
