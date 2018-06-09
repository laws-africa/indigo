from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse


from indigo_api.models import Document, Subtype, Work, Amendment
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
    works = Work.objects.filter(country=doc.country)
    works_json = json.dumps(serializer.to_representation(works))

    amendments_json = json.dumps(
        WorkAmendmentSerializer(context={'request': request}, many=True)
        .to_representation(doc.work.amendments))

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
        'work': doc.work,
        'work_json': work_json,
        'works_json': works_json,
        'amendments_json': amendments_json,
        'form': form,
        'subtypes': Subtype.objects.order_by('name').all(),
        'languages': Language.objects.select_related('language').all(),
        'countries': countries,
        'countries_json': countries_json,
        'view': 'DocumentView',
    })


@login_required
def edit_work(request, frbr_uri=None):
    if frbr_uri:
        print frbr_uri
        work = get_object_or_404(Work, frbr_uri=frbr_uri)
        work_json = json.dumps(WorkSerializer(instance=work, context={'request': request}).data)
        country_code = work.country
        locality = work.locality
    else:
        # it's new!
        work = None
        work_json = {}
        country_code = request.user.editor.country_code
        locality = None

    country = Country.objects.select_related('country').filter(country__iso__iexact=country_code).first()
    if locality:
        locality = country.locality_set.filter(code=locality).first()

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
def work_amendments(request, frbr_uri):
    work = get_object_or_404(Work, frbr_uri=frbr_uri)
    work_json = json.dumps(WorkSerializer(instance=work, context={'request': request}).data)

    country = Country.objects.select_related('country').filter(country__iso__iexact=work.country)[0]
    locality = None
    if work.locality:
        locality = country.locality_set.filter(code=work.locality)[0]

    docs = DocumentViewSet.queryset.filter(work=work).all()
    serializer = DocumentSerializer(context={'request': request}, many=True)
    documents_json = json.dumps(serializer.to_representation(docs))

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
        'documents_json': documents_json,
        'view': 'WorkAmendmentsView',
    })


@login_required
def work_related(request, frbr_uri):
    work = get_object_or_404(Work, frbr_uri=frbr_uri)
    work_json = json.dumps(WorkSerializer(instance=work, context={'request': request}).data)

    country = Country.for_work(work)
    locality = country.work_locality(work)

    # parents and children
    family = []
    if work.parent_work:
        family.append({
            'rel': 'child of',
            'work': work.parent_work,
        })
    family = family + [{
        'rel': 'parent of',
        'work': w,
    } for w in work.child_works.all()]

    # amended works
    amended = Amendment.objects.filter(amending_work=work).prefetch_related('amended_work').order_by('amended_work__frbr_uri').all()
    amended = [{
        'rel': 'amends',
        'work': a.amended_work,
    } for a in amended]

    # amending works
    amended_by = Amendment.objects.filter(amended_work=work).prefetch_related('amending_work').order_by('amending_work__frbr_uri').all()
    amended_by = [{
        'rel': 'amended by',
        'work': a.amending_work,
    } for a in amended_by]

    # repeals
    repeals = []
    if work.repealed_by:
        repeals.append({
            'rel': 'repealed by',
            'work': work.repealed_by,
        })
    repeals = repeals + [{
        'rel': 'repeals',
        'work': w,
    } for w in work.repealed_works.all()]

    # commencement
    commencement = []
    if work.commencing_work:
        commencement.append({
            'rel': 'commenced by',
            'work': work.commencing_work,
        })
    commencement = commencement + [{
        'rel': 'commenced',
        'work': w,
    } for w in work.commenced_works.all()]

    no_related = (not family and not amended and not amended_by and not repeals and not commencement)

    return render(request, 'work/related.html', {
        'country': country,
        'locality': locality,
        'work': work,
        'work_json': work_json,
        'family': family,
        'amended': amended,
        'amended_by': amended_by,
        'repeals': repeals,
        'commencement': commencement,
        'no_related': no_related,
        'view': '',
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
def library(request, country=None):
    if country is None:
        return HttpResponseRedirect(reverse('library', kwargs={'country': request.user.editor.country_code}))

    countries = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
    countries_json = json.dumps({c.code: c.as_json() for c in countries})

    serializer = DocumentListSerializer(context={'request': request})
    docs = DocumentViewSet.queryset.filter(country=country)
    documents_json = json.dumps(serializer.to_representation(docs))

    serializer = WorkSerializer(context={'request': request}, many=True)
    works = Work.objects.filter(country=country)
    works_json = json.dumps(serializer.to_representation(works))

    return render(request, 'library.html', {
        'countries': countries,
        'countries_json': countries_json,
        'documents_json': documents_json,
        'works_json': works_json,
        'countries': countries,
        'country_code': country,
        'view': 'LibraryView',
    })
