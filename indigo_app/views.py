from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse


from indigo_api.models import Document, Subtype, Work
from indigo_api.serializers import DocumentSerializer, DocumentListSerializer, WorkSerializer, WorkAmendmentSerializer
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
        frbr_uri = request.GET.get('frbr_uri')
        if not frbr_uri:
            return HttpResponseRedirect(reverse('library'))

        try:
            doc = Document.randomized(frbr_uri)
        except ValueError:
            # bad url
            return HttpResponseRedirect(reverse('library'))

        doc.tags = None
        doc_json = json.dumps(DocumentSerializer(instance=doc, context={'request': request}).data)

    work_json = json.dumps(WorkSerializer(instance=doc.work, context={'request': request}).data)
    serializer = WorkSerializer(context={'request': request}, many=True)
    works = Work.objects.undeleted().filter(country=doc.country)
    works_json = json.dumps(serializer.to_representation(works))

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
        'works_json': works_json,
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

    country = Country.objects.select_related('country').filter(country__iso__iexact=work.country)[0]
    locality = None
    if work.locality:
        locality = country.locality_set.filter(code=work.locality)[0]

    countries = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
    countries_json = json.dumps({c.code: c.as_json() for c in countries})

    return render(request, 'work/edit.html', {
        'work': work,
        'work_json': work_json,
        'subtypes': Subtype.objects.order_by('name').all(),
        'languages': Language.objects.select_related('language').all(),
        'country': country,
        'locality': locality,
        'countries': countries,
        'countries_json': countries_json,
        'view': 'WorkView',
    })


@login_required
def work_amendments(request, work_id):
    work = get_object_or_404(Work, pk=work_id)
    if work.deleted:
        raise Http404()
    work_json = json.dumps(WorkSerializer(instance=work, context={'request': request}).data)

    country = Country.objects.select_related('country').filter(country__iso__iexact=work.country)[0]
    locality = None
    if work.locality:
        locality = country.locality_set.filter(code=work.locality)[0]

    countries = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
    countries_json = json.dumps({c.code: c.as_json() for c in countries})

    serializer = WorkAmendmentSerializer(context={'request': request}, many=True)
    amendments = work.amendments.prefetch_related('created_by_user', 'updated_by_user', 'amending_work')
    amendments_json = json.dumps(serializer.to_representation(amendments))

    return render(request, 'work/amendments.html', {
        'country': country,
        'locality': locality,
        'amendments_json': amendments_json,
        'work': work,
        'work_json': work_json,
        'countries': countries,
        'countries_json': countries_json,
        'view': 'WorkAmendmentsView',
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
    docs = DocumentViewSet.queryset.filter(country=request.user.editor.country_code)
    documents_json = json.dumps(serializer.to_representation(docs))

    serializer = WorkSerializer(context={'request': request}, many=True)
    works = Work.objects.undeleted().filter(country=request.user.editor.country_code)
    works_json = json.dumps(serializer.to_representation(works))

    return render(request, 'library.html', {
        'countries': countries,
        'countries_json': countries_json,
        'documents_json': documents_json,
        'works_json': works_json,
        'countries': countries,
        'view': 'LibraryView',
    })
