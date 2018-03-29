from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404


from indigo_api.models import Document, Subtype, Work
from indigo_api.serializers import DocumentSerializer, DocumentListSerializer, WorkSerializer
from indigo_api.views.documents import DocumentViewSet
from indigo_app.models import Language, Country
from .forms import DocumentForm
import json


@login_required
def document(request, doc_id=None):
    if doc_id:
        doc = get_object_or_404(Document, pk=doc_id)
        if doc.deleted:
            raise Http404()
        # don't serialize this doc, we'll get it from the library
        doc_json = json.dumps(None)
    else:
        # it's new!
        doc = Document.randomized(request.user, title='(untitled)')
        doc.tags = None
        doc_json = json.dumps(DocumentSerializer(instance=doc, context={'request': request}).data)

    work_json = json.dumps(WorkSerializer(instance=doc.work, context={'request': request}).data)

    form = DocumentForm(instance=doc)

    countries = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
    countries_json = json.dumps({c.code: c.as_json() for c in countries})

    serializer = DocumentListSerializer(context={'request': request})
    documents_json = json.dumps(serializer.to_representation(DocumentViewSet.queryset.all()))

    return render(request, 'document/show.html', {
        'document': doc,
        'document_json': doc_json,
        'document_content_json': json.dumps(doc.document_xml),
        'documents_json': documents_json,
        'work_json': work_json,
        'form': form,
        'subtypes': Subtype.objects.order_by('name').all(),
        'languages': Language.objects.select_related('language').all(),
        'countries': countries,
        'countries_json': countries_json,
        'view': 'DocumentView',
    })


@login_required
def edit_work(request, work_id=None):
    if work_id:
        work = get_object_or_404(Work, pk=work_id)
        if work.deleted:
            raise Http404()
        work_json = json.dumps(WorkSerializer(instance=work, context={'request': request}).data)
    else:
        # it's new!
        work = None
        work_json = {}

    countries = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
    countries_json = json.dumps({c.code: c.as_json() for c in countries})

    return render(request, 'work/edit.html', {
        'work': work,
        'work_json': work_json,
        'subtypes': Subtype.objects.order_by('name').all(),
        'languages': Language.objects.select_related('language').all(),
        'countries': countries,
        'countries_json': countries_json,
        'view': 'WorkView',
    })


@login_required
def import_document(request):
    frbr_uri = request.GET.get('frbr_uri')
    doc = Document(frbr_uri=frbr_uri or '/')

    form = DocumentForm(instance=doc)
    countries = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
    countries_json = json.dumps({c.code: c.as_json() for c in countries})

    work = None
    work_json = None

    if frbr_uri:
        try:
            work = Work.objects.get_for_frbr_uri(frbr_uri)
            work_json = json.dumps(WorkSerializer(instance=work, context={'request': request}).data)
        except ValueError:
            pass

    return render(request, 'import.html', {
        'document': doc,
        'form': form,
        'countries': countries,
        'countries_json': countries_json,
        'frbr_uri': frbr_uri,
        'work': work,
        'work_json': work_json,
        'view': 'ImportView',
    })


@login_required
def library(request):
    countries = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
    countries_json = json.dumps({c.code: c.as_json() for c in countries})

    serializer = DocumentListSerializer(context={'request': request})
    documents_json = json.dumps(serializer.to_representation(DocumentViewSet.queryset.all()))

    return render(request, 'library.html', {
        'countries_json': countries_json,
        'documents_json': documents_json,
        'countries': countries,
        'view': 'LibraryView',
    })
