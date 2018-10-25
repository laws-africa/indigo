# coding=utf-8
import json
import io
import re
import logging

from django.core.exceptions import ValidationError
from django.contrib import messages
from django.views.generic import DetailView, TemplateView, FormView, UpdateView, CreateView
from django.views.generic.edit import BaseFormView
from django.views.generic.list import MultipleObjectMixin
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from reversion import revisions as reversion
from cobalt.act import FrbrUri
import datetime
import requests
import unicodecsv as csv

from indigo.plugins import plugins
from indigo_api.models import Subtype, Work, Amendment, Country, Document
from indigo_api.serializers import WorkSerializer, DocumentSerializer, AttachmentSerializer
from indigo_api.views.documents import DocumentViewSet
from indigo_api.views.works import WorkViewSet
from indigo_api.signals import work_changed
from indigo_app.revisions import decorate_versions
from indigo_app.forms import BatchCreateWorkForm, ImportDocumentForm

from .base import AbstractAuthedIndigoView


log = logging.getLogger(__name__)


class LibraryView(AbstractAuthedIndigoView, TemplateView):
    template_name = 'library.html'
    # permissions
    permission_required = ('indigo_api.view_work',)
    check_country_perms = False

    def get(self, request, country=None, *args, **kwargs):
        if country is None:
            return redirect('library', country=request.user.editor.country_code)
        return super(LibraryView, self).get(request, country_code=country, *args, **kwargs)

    def get_context_data(self, country_code, **kwargs):
        context = super(LibraryView, self).get_context_data(**kwargs)

        country = Country.for_code(country_code)
        context['country'] = country
        context['country_code'] = country_code
        context['countries'] = Country.objects.select_related('country').prefetch_related('localities', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in context['countries']})

        serializer = DocumentSerializer(context={'request': self.request}, many=True)
        docs = DocumentViewSet.queryset.filter(work__country=country)
        context['documents_json'] = json.dumps(serializer.to_representation(docs))

        serializer = WorkSerializer(context={'request': self.request}, many=True)
        works = WorkViewSet.queryset.filter(country=country)
        context['works_json'] = json.dumps(serializer.to_representation(works))

        return context


class AbstractWorkDetailView(AbstractAuthedIndigoView, DetailView):
    model = Work
    context_object_name = 'work'
    # load work based on the frbr_uri
    pk_url_kwarg = None
    slug_url_kwarg = 'frbr_uri'
    slug_field = 'frbr_uri'

    # permissions
    permission_required = ('indigo_api.view_work',)
    check_country_perms = True

    @property
    def work(self):
        return self.object

    def get_country(self):
        return self.get_object().country

    def get_context_data(self, **kwargs):
        context = super(AbstractWorkDetailView, self).get_context_data(**kwargs)

        is_new = not self.work.frbr_uri

        context['work_json'] = {} if is_new else json.dumps(WorkSerializer(instance=self.work, context={'request': self.request}).data)
        context['country'] = self.work.country
        context['locality'] = None if is_new else context['country'].work_locality(self.work)

        # TODO do this in a better place
        context['countries'] = Country.objects.select_related('country').prefetch_related('localities', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in context['countries']})
        context['subtypes'] = Subtype.objects.order_by('name').all()

        return context


class WorkDetailView(AbstractWorkDetailView):
    js_view = 'WorkDetailView'


class AddWorkView(WorkDetailView):
    def get_object(self, queryset=None):
        work = Work()
        work.country = self.request.user.editor.country
        return work


class WorkOverviewView(AbstractWorkDetailView):
    js_view = ''
    template_name_suffix = '_overview'

    def get_context_data(self, **kwargs):
        context = super(WorkOverviewView, self).get_context_data(**kwargs)

        context['versions'] = decorate_versions(self.work.versions()[:3])

        return context


class WorkAmendmentsView(AbstractWorkDetailView):
    template_name_suffix = '_amendments'


class WorkDependentMixin(object):
    """ Mixin for views that hang off a work URL, using the frbr_uri URL kwarg.
    """
    _work = None
    check_country_perms = True

    @property
    def work(self):
        if not self._work:
            self._work = get_object_or_404(Work, frbr_uri=self.kwargs['frbr_uri'])
        return self._work

    def get_country(self):
        return self.work.country


class WorkAmendmentDetailView(AbstractAuthedIndigoView, WorkDependentMixin, UpdateView):
    """ View to update or delete amendment.
    """
    http_method_names = ['post']
    model = Amendment
    pk_url_kwarg = 'amendment_id'
    fields = ['date']

    def get_queryset(self):
        return self.work.amendments

    def get_permission_required(self):
        if 'delete' in self.request.POST:
            return ('indigo_api.delete_amendment',)
        return ('indigo_api.change_amendment',)

    def post(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            return self.delete(request, *args, **kwargs)
        return super(WorkAmendmentDetailView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        # get old/existing/incorrect date
        old_date = form.initial['date']

        # do normal things to amend work
        result = super(WorkAmendmentDetailView, self).form_valid(form)
        self.object.updated_by_user = self.request.user
        self.object.save()

        # update old docs to have the new date as their expression date
        docs = Document.objects.filter(work=self.object.amended_work, expression_date=old_date)
        for doc in docs:
            doc.expression_date = self.object.date
            doc.save()

        return result

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.can_delete():
            self.object.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        url = reverse('work_amendments', kwargs={'frbr_uri': self.kwargs['frbr_uri']})
        if self.object.id:
            url += "#amendment-%s" % self.object.id
        return url


class AddWorkAmendmentView(AbstractAuthedIndigoView, WorkDependentMixin, CreateView):
    """ View to add a new amendment.
    """
    model = Amendment
    fields = ['date', 'amending_work']
    permission_required = ('indigo_api.add_amendment',)

    def get_form_kwargs(self):
        kwargs = super(AddWorkAmendmentView, self).get_form_kwargs()
        kwargs['instance'] = Amendment(amended_work=self.work)
        kwargs['instance'].created_by_user = self.request.user
        kwargs['instance'].updated_by_user = self.request.user
        return kwargs

    def form_invalid(self, form):
        return redirect(self.get_success_url())

    def get_success_url(self):
        url = reverse('work_amendments', kwargs={'frbr_uri': self.kwargs['frbr_uri']})
        if self.object:
            url = url + "#amendment-%s" % self.object.id
        return url


class AddWorkPointInTimeView(AbstractAuthedIndigoView, WorkDependentMixin, CreateView):
    """ View to get or create a new point-in-time for a work, at a particular date
    and in a particular language.
    """
    model = Document
    fields = ['expression_date', 'language']
    permission_required = ('indigo_api.add_document',)

    def form_valid(self, form):
        date = form.cleaned_data['expression_date']
        language = form.cleaned_data['language']

        # does one already exist?
        doc = self.work.expressions().filter(expression_date=date, language=language).first()
        if not doc:
            # create a new one
            doc = self.work.create_expression_at(date, language)

        return redirect('document', doc_id=doc.id)


class WorkRelatedView(AbstractWorkDetailView):
    js_view = ''
    template_name_suffix = '_related'

    def get_context_data(self, **kwargs):
        context = super(WorkRelatedView, self).get_context_data(**kwargs)

        # parents and children
        family = []
        if self.work.parent_work:
            family.append({
                'rel': 'child of',
                'work': self.work.parent_work,
            })
        family = family + [{
            'rel': 'parent of',
            'work': w,
        } for w in self.work.child_works.all()]
        context['family'] = family

        # amended works
        amended = Amendment.objects.filter(amending_work=self.work).prefetch_related('amended_work').order_by('amended_work__frbr_uri').all()
        amended = [{
            'rel': 'amends',
            'work': a.amended_work,
        } for a in amended]
        context['amended'] = amended

        # amending works
        amended_by = Amendment.objects.filter(amended_work=self.work).prefetch_related('amending_work').order_by('amending_work__frbr_uri').all()
        amended_by = [{
            'rel': 'amended by',
            'work': a.amending_work,
        } for a in amended_by]
        context['amended_by'] = amended_by

        # repeals
        repeals = []
        if self.work.repealed_by:
            repeals.append({
                'rel': 'repealed by',
                'work': self.work.repealed_by,
            })
        repeals = repeals + [{
            'rel': 'repeals',
            'work': w,
        } for w in self.work.repealed_works.all()]
        context['repeals'] = repeals

        # commencement
        commencement = []
        if self.work.commencing_work:
            commencement.append({
                'rel': 'commenced by',
                'work': self.work.commencing_work,
            })
        commencement = commencement + [{
            'rel': 'commenced',
            'work': w,
        } for w in self.work.commenced_works.all()]
        context['commencement'] = commencement

        context['no_related'] = (not family and not amended and not amended_by and not repeals and not commencement)

        return context


class WorkVersionsView(AbstractWorkDetailView, MultipleObjectMixin):
    js_view = ''
    template_name_suffix = '_versions'
    object_list = None
    page_size = 20

    def get_context_data(self, **kwargs):
        context = super(WorkVersionsView, self).get_context_data(**kwargs)

        paginator, page, versions, is_paginated = self.paginate_queryset(self.work.versions(), self.page_size)
        context.update({
            'paginator': paginator,
            'page': page,
            'is_paginated': is_paginated,
            'versions': decorate_versions(versions),
        })

        return context


class RestoreWorkVersionView(AbstractWorkDetailView):
    http_method_names = ['post']
    permission_required = ('indigo_api.change_work',)

    def post(self, request, frbr_uri, version_id):
        self.object = self.get_object()
        version = self.work.versions().filter(pk=version_id).first()
        if not version:
            raise Http404()

        with reversion.create_revision():
            reversion.set_user(request.user)
            reversion.set_comment("Restored version %s" % version.id)
            version.revert()
        messages.success(request, 'Restored version %s' % version.id)

        # signals
        work_changed.send(sender=self.work.__class__, work=self.work, request=request)

        url = request.GET.get('next') or reverse('work', kwargs={'frbr_uri': self.work.frbr_uri})
        return redirect(url)


class BatchAddWorkView(AbstractAuthedIndigoView, FormView):
    template_name = 'indigo_api/work_new_batch.html'
    # permissions
    permission_required = ('indigo_api.add_work',)
    form_class = BatchCreateWorkForm

    def form_valid(self, form):
        country = form.cleaned_data['country']
        table = self.get_table(form.cleaned_data['spreadsheet_url'])
        works = self.get_works(country, table)
        return self.render_to_response(self.get_context_data(works=works))

    def get_country(self):
        pk = self.request.POST.get('country')
        if pk:
            return get_object_or_404(Country, pk=pk)
        else:
            return self.request.user.editor.country

    def get_works(self, country, table):
        works = []

        # clean up headers
        headers = [h.split(' ')[0].lower() for h in table[0]]

        # transform rows into list of dicts for easy access
        rows = [
            {header: row[i] for i, header in enumerate(headers) if header}
            for row in table[1:]
        ]

        for idx, row in enumerate(rows):
            if not row['ignore']:
                info = {
                    'row': idx + 2,
                }
                works.append(info)

                try:
                    frbr_uri = self.get_frbr_uri(country, row)
                except ValueError as e:
                    info['status'] = 'error'
                    info['error_message'] = e.message
                    continue

                try:
                    work = Work.objects.get(frbr_uri=frbr_uri)
                    info['work'] = work
                    info['status'] = 'duplicate'

                # TODO one day: also mark first work as duplicate if user is trying to import two of the same (currently only the second one will be)

                except Work.DoesNotExist:
                    work = Work()

                    work.frbr_uri = frbr_uri
                    work.title = row['title']
                    work.country = country
                    work.publication_name = row['publication_name']
                    work.publication_number = row['publication_number']
                    work.publication_date = self.make_date(row['publication_date'])
                    work.commencement_date = self.make_date(row['commencement_date'])
                    work.assent_date = self.make_date(row['assent_date'])
                    work.created_by_user = self.request.user
                    work.updated_by_user = self.request.user

                    try:
                        work.full_clean()
                        work.save()

                        # signals
                        work_changed.send(sender=work.__class__, work=work, request=self.request)

                        info['status'] = 'success'
                        info['work'] = work

                    except ValidationError as e:
                        info['status'] = 'error'
                        info['error_message'] = ' '.join(['%s: %s' % (f, '; '.join(errs)) for f, errs in e.message_dict.items()])

        return works

    def get_table(self, spreadsheet_url):
        # get list of lists where each inner list is a row in a spreadsheet
        # TODO: display the ValidationError strings within the form instead (as with URLValidator in .forms message)

        match = re.match('^https://docs.google.com/spreadsheets/d/(\S+)/', spreadsheet_url)

        # not sure this is doing anything? URLValidator picking this type of issue up already?
        if not match:
            raise ValidationError("Unable to extract key from Google Sheets URL")

        try:
            url = 'https://docs.google.com/spreadsheets/d/%s/export?format=csv' % match.group(1)
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValidationError("Error talking to Google Sheets: %s" % e.message)

        rows = csv.reader(io.BytesIO(response.content), encoding='utf-8')
        rows = list(rows)

        if not rows or not rows[0]:
            raise ValidationError("Your sheet did not import successfully; please check that it is 'Published to the web' and shared with 'Anyone with the link'")
        else:
            return rows

    def get_frbr_uri(self, country, row):
        frbr_uri = FrbrUri(country=row['country'], locality=row['locality'], doctype='act', subtype=row['subtype'], date=row['year'], number=row['number'], actor=None)

        # check country matches (and that it's all one country)
        if country.code != row['country'].lower():
            raise ValueError('The country in the spreadsheet (%s) doesn\'t match the country selected previously (%s)' % (row['country'], country))

        # check all frbr uri fields have been filled in and that no spaces were accidentally included
        if ' ' in frbr_uri.work_uri():
            raise ValueError('Check for spaces in country, locality, subtype, year, number – none allowed')
        elif not frbr_uri.country:
            raise ValueError('A country must be given')
        elif not frbr_uri.date:
            raise ValueError('A year must be given')
        elif not frbr_uri.number:
            raise ValueError('A number must be given')

        # check that necessary work fields have been filled in
        elif not row['title']:
            raise ValueError('A title must be given')
        elif not row['publication_date']:
            raise ValueError('A publication date must be given')

        return frbr_uri.work_uri().lower()

    def make_date(self, string):
        if string == '':
            date = None
        else:
            date = datetime.datetime.strptime(string, '%Y-%m-%d')
        return date


class ImportDocumentView(AbstractWorkDetailView, BaseFormView):
    """ View to import a document as an expression for a work.

    This behaves a bit differently to normal form submission. The client
    submits the form via AJAX. If it's a success, we send them the location
    to go to. If not, we send them form errors.

    This gives a better experience than submitting the form natively, because
    it allows us to handle errors without refreshing the whole page.
    """
    template_name = 'indigo_api/work_import_document.html'
    permission_required = ('indigo_api.view_work', 'indigo_api.add_document')
    js_view = 'ImportView'
    form_class = ImportDocumentForm

    def get_initial(self):
        try:
            date = datetime.datetime.strptime(self.request.GET.get('expression_date', ''), '%Y-%m-%d').date
        except ValueError:
            date = None

        return {
            'language': self.work.country.primary_language,
            'expression_date': date or datetime.date.today(),
        }

    def get_context_data(self, **kwargs):
        kwargs = super(ImportDocumentView, self).get_context_data(**kwargs)
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(ImportDocumentView, self).post(request, *args, **kwargs)

    def form_invalid(self, form):
        return JsonResponse(form.errors, status=400)

    def form_valid(self, form):
        data = form.cleaned_data
        upload = data['file']
        opts = data.get('options', {})

        document = Document()
        document.work = self.work
        document.expression_date = data['expression_date']
        document.language = data['language']
        document.save()

        importer = plugins.for_document('importer', document)
        importer.section_number_position = opts.get('section_number_position', 'guess')

        importer.cropbox = opts.get('cropbox', None)

        try:
            importer.create_from_upload(upload, document, self.request)
        except ValueError as e:
            log.error("Error during import: %s" % e.message, exc_info=e)
            raise ValidationError(e.message or "error during import")

        document.created_by_user = self.request.user
        document.updated_by_user = self.request.user
        document.save()

        # add source file as an attachment
        AttachmentSerializer(context={'document': document}).create({'file': upload})

        return JsonResponse({'location': reverse('document', kwargs={'doc_id': document.id})})
