from django.shortcuts import render, get_object_or_404

from indigo_api.models import Document, Subtype
from indigo_api.serializers import DocumentSerializer, DocumentListSerializer
from indigo_api.views import DocumentViewSet
from indigo_app.models import Language, Country
from .forms import DocumentForm
import json


def document(request, doc_id=None):
    if doc_id:
        doc = get_object_or_404(Document, pk=doc_id)
        doc_json = json.dumps(None)
    else:
        # it's new!
        doc = Document.randomized(request.user, title='(untitled)')
        doc.tags = None
        doc_json = json.dumps(DocumentSerializer(instance=doc, context={'request': request}).data)

    form = DocumentForm(instance=doc)

    countries = Country.objects.select_related('country').prefetch_related('locality_set', 'country').all()
    countries = {c.code: c.as_json() for c in countries}
    countries_json = json.dumps(countries)

    serializer = DocumentListSerializer(context={'request': request})
    documents_json = json.dumps(serializer.to_representation(DocumentViewSet.queryset.all()))

    return render(request, 'document/show.html', {
        'document': doc,
        'document_json': doc_json,
        'document_content_json': json.dumps(doc.document_xml),
        'documents_json': documents_json,
        'form': form,
        'subtypes': Subtype.objects.order_by('name').all(),
        'languages': Language.objects.select_related('language').all(),
        'countries': Country.objects.select_related('country').all(),
        'countries_json': countries_json,
        'view': 'DocumentView',
    })


def import_document(request):
    doc = Document(frbr_uri='/')
    form = DocumentForm(instance=doc)
    return render(request, 'import.html', {
        'document': doc,
        'form': form,
        'countries': Country.objects.select_related('country').all(),
        'view': 'ImportView',
    })


def library(request):
    countries = Country.objects.select_related('country').prefetch_related('locality_set', 'country').all()
    countries = {c.code: c.as_json() for c in countries}
    countries_json = json.dumps(countries)

    serializer = DocumentListSerializer(context={'request': request})
    documents_json = json.dumps(serializer.to_representation(DocumentViewSet.queryset.all()))

    return render(request, 'library.html', {
        'countries_json': countries_json,
        'documents_json': documents_json,
        'countries': Country.objects.select_related('country').all(),
        'view': 'LibraryView',
    })


def password_reset_confirm(request, uidb64, token):
    return render(request, 'user/password_reset_confirm.html', {
        'uid': uidb64,
        'token': token,
    })
