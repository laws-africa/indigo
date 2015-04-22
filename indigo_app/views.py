from django.shortcuts import render, get_object_or_404

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


def import_document(request):
    doc = Document(frbr_uri='/')
    form = DocumentForm(instance=doc)
    return render(request, 'import.html', {
        'document': doc,
        'form': form,
        'view': 'ImportView',
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
