# coding=utf-8
import json
import io
import re

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.views.generic import DetailView, TemplateView, FormView
from django.views.generic.list import MultipleObjectMixin
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect
from reversion import revisions as reversion

from cobalt.act import FrbrUri
from datetime import datetime
import requests
import unicodecsv as csv

from indigo_api.models import Document, Subtype, Work, Amendment
from indigo_api.serializers import DocumentSerializer, WorkSerializer, WorkAmendmentSerializer
from indigo_api.views.documents import DocumentViewSet
from indigo_api.signals import work_changed
from indigo_app.models import Language, Country
from indigo_app.revisions import decorate_versions
from indigo_app.forms import DocumentForm, UserForm, BatchCreateWorkForm


class IndigoJSViewMixin(object):
    """ View that inject's the appropriate Backbone view name into the template, for use by the Backbone
    view system. By default, the Backbone view name is the same name as the view's class name.
    Set `js_view` to another name to change it, or the empty string to disable completely.
    """
    js_view = None

    def get_context_data(self, **kwargs):
        context = super(IndigoJSViewMixin, self).get_context_data(**kwargs)
        context['js_view'] = self.get_js_view()
        return context

    def get_js_view(self):
        if self.js_view is None:
            return self.__class__.__name__
        return self.js_view


class AbstractAuthedIndigoView(PermissionRequiredMixin, IndigoJSViewMixin):
    """ Abstract view for authenticated Indigo views.
    """
    # permissions
    raise_exception = True
    permission_required = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
        return super(AbstractAuthedIndigoView, self).dispatch(request, *args, **kwargs)


class LibraryView(AbstractAuthedIndigoView, TemplateView):
    template_name = 'library.html'
    # permissions
    permission_required = ('indigo_api.view_work',)

    def get(self, request, country=None, *args, **kwargs):
        if country is None:
            return HttpResponseRedirect(reverse('library', kwargs={'country': request.user.editor.country_code}))
        return super(LibraryView, self).get(request, country=country, *args, **kwargs)

    def get_context_data(self, country, **kwargs):
        context = super(LibraryView, self).get_context_data(**kwargs)

        context['country_code'] = country
        context['countries'] = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in context['countries']})

        serializer = DocumentSerializer(context={'request': self.request}, many=True)
        docs = DocumentViewSet.queryset.filter(country=country)
        context['documents_json'] = json.dumps(serializer.to_representation(docs))

        serializer = WorkSerializer(context={'request': self.request}, many=True)
        works = Work.objects.filter(country=country)
        context['works_json'] = json.dumps(serializer.to_representation(works))

        return context


class AbstractWorkView(AbstractAuthedIndigoView, DetailView):
    model = Work
    context_object_name = 'work'
    # load work based on the frbr_uri
    pk_url_kwarg = None
    slug_url_kwarg = 'frbr_uri'
    slug_field = 'frbr_uri'

    # permissions
    permission_required = ('indigo_api.view_work',)

    def get_context_data(self, **kwargs):
        context = super(AbstractWorkView, self).get_context_data(**kwargs)

        work = self.object
        is_new = not work.frbr_uri

        context['work_json'] = {} if is_new else json.dumps(WorkSerializer(instance=work, context={'request': self.request}).data)
        context['country'] = Country.for_work(work)
        context['locality'] = None if is_new else context['country'].work_locality(work)

        # TODO do this in a better place
        context['countries'] = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in context['countries']})
        context['subtypes'] = Subtype.objects.order_by('name').all()

        return context


class WorkDetailView(AbstractWorkView):
    js_view = 'WorkDetailView'


class AddWorkView(WorkDetailView):
    def get_object(self, *args, **kwargs):
        work = Work()
        work.country = self.request.user.editor.country_code
        return work


class WorkOverviewView(AbstractWorkView):
    js_view = ''
    template_name_suffix = '_overview'

    def get_context_data(self, **kwargs):
        context = super(WorkOverviewView, self).get_context_data(**kwargs)

        work = self.object
        context['versions'] = decorate_versions(work.versions()[:3])

        return context


class WorkAmendmentsView(AbstractWorkView):
    template_name_suffix = '_amendments'

    def get_context_data(self, **kwargs):
        context = super(WorkAmendmentsView, self).get_context_data(**kwargs)

        work = self.object

        docs = DocumentViewSet.queryset.filter(work=work).all()
        serializer = DocumentSerializer(context={'request': self.request}, many=True)
        context['documents_json'] = json.dumps(serializer.to_representation(docs))

        serializer = WorkAmendmentSerializer(context={'request': self.request}, many=True)
        amendments = work.amendments.prefetch_related('created_by_user', 'updated_by_user', 'amending_work')
        context['amendments_json'] = json.dumps(serializer.to_representation(amendments))

        return context


class WorkRelatedView(AbstractWorkView):
    js_view = ''
    template_name_suffix = '_related'

    def get_context_data(self, **kwargs):
        context = super(WorkRelatedView, self).get_context_data(**kwargs)

        work = self.object

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
        context['family'] = family

        # amended works
        amended = Amendment.objects.filter(amending_work=work).prefetch_related('amended_work').order_by('amended_work__frbr_uri').all()
        amended = [{
            'rel': 'amends',
            'work': a.amended_work,
        } for a in amended]
        context['amended'] = amended

        # amending works
        amended_by = Amendment.objects.filter(amended_work=work).prefetch_related('amending_work').order_by('amending_work__frbr_uri').all()
        amended_by = [{
            'rel': 'amended by',
            'work': a.amending_work,
        } for a in amended_by]
        context['amended_by'] = amended_by

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
        context['repeals'] = repeals

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
        context['commencement'] = commencement

        context['no_related'] = (not family and not amended and not amended_by and not repeals and not commencement)

        return context


class WorkVersionsView(AbstractWorkView, MultipleObjectMixin):
    js_view = ''
    template_name_suffix = '_versions'
    object_list = None
    page_size = 20

    def get_context_data(self, **kwargs):
        context = super(WorkVersionsView, self).get_context_data(**kwargs)
        work = self.object

        paginator, page, versions, is_paginated = self.paginate_queryset(work.versions(), self.page_size)
        context.update({
            'paginator': paginator,
            'page': page,
            'is_paginated': is_paginated,
            'versions': decorate_versions(versions),
        })

        return context


class RestoreWorkVersionView(AbstractWorkView):
    http_method_names = ['post']
    permission_required = ('indigo_api.change_work',)

    def post(self, request, frbr_uri, version_id):
        work = self.get_object()
        version = work.versions().filter(pk=version_id).first()
        if not version:
            raise Http404()

        with reversion.create_revision():
            reversion.set_user(request.user)
            reversion.set_comment("Restored version %s" % version.id)
            version.revert()
        messages.success(request, 'Restored version %s' % version.id)

        # signals
        work_changed.send(sender=work.__class__, work=work, request=request)

        url = request.GET.get('next') or reverse('work', kwargs={'frbr_uri': work.frbr_uri})
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
                work.country = country.code
                work.publication_name = row['publication_name']
                work.publication_number = row['publication_number']
                work.publication_date = self.make_date(row['publication_date'])
                work.commencement_date = self.make_date(row['commencement_date'])
                work.assent_date = self.make_date(row['assent_date'])
                work.repealed_date = self.make_date(row['repealed_date'])
                work.created_by_user = self.request.user
                work.updated_by_user = self.request.user

                try:
                    work.full_clean()
                    work.save()
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
        # TODO: remove municipality name when by-law
        try:
            int(row['number'])
            number = row['number']
        except ValueError:
            number = row['title']
            number = re.sub(", [0-9]{2,}", "", number)
            number = number.replace(' ', '-').replace(',', '').replace('-Act', '').replace('Act-', '').lower().replace('relating-to-', '').replace('-and-', '-').replace('-to-', '-').replace('-of-', '-').replace('-for-', '-').replace('-on-', '-').replace('-the-', '-').replace('in-connection-with-', '').replace('by-law-', '').replace('-by-law', '')

        frbr_uri = FrbrUri(country=row['country'], locality=row['locality'], doctype=row['doctype'], subtype=row['subtype'], date=row['date'], number=number, actor=None)

        # TODO: simplify this somehow?

        if country.code != row['country'].lower():
            raise ValueError('The country in the spreadsheet (%s) doesn\'t match the country selected previously (%s)' % (row['country'], country))
        if ' ' in frbr_uri.work_uri():
            raise ValueError('Check for spaces in grey columns – none allowed')
        elif not frbr_uri.country:
            raise ValueError('A country must be specified')
        elif not frbr_uri.doctype:
            raise ValueError('A doctype must be specified – use \'Act\' if unsure')
        elif not frbr_uri.date:
            raise ValueError('A date must be specified')
        elif not frbr_uri.number:
            raise ValueError('A number must be specified')

        return frbr_uri.work_uri().lower()

    def make_date(self, string):
        if string == '':
            date = None
        else:
            date = datetime.strptime(string, '%Y-%m-%d')
        return date


class ImportDocumentView(AbstractWorkView):
    template_name = 'work/import_document.html'
    permission_required = ('indigo_api.view_work', 'indigo_api.add_document')
    js_view = 'ImportView'

    def get_context_data(self, **kwargs):
        context = super(ImportDocumentView, self).get_context_data(**kwargs)

        work = self.object
        doc = Document(frbr_uri=work.frbr_uri or '/')
        context['document'] = doc
        context['form'] = DocumentForm(instance=doc)

        return context


class DocumentDetailView(AbstractAuthedIndigoView, DetailView):
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'document/show.html'

    # permissions
    permission_required = ('indigo_api.view_work',)

    def get_object(self, queryset=None):
        doc = super(DocumentDetailView, self).get_object(queryset)
        if doc.deleted:
            raise Http404()
        return doc

    def get_context_data(self, **kwargs):
        context = super(DocumentDetailView, self).get_context_data(**kwargs)

        doc = self.object

        context['work'] = doc.work
        context['work_json'] = json.dumps(WorkSerializer(instance=doc.work, context={'request': self.request}).data)
        context['country'] = Country.for_work(doc.work)
        context['locality'] = context['country'].work_locality(doc.work)

        # TODO do this in a better place
        context['countries'] = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in context['countries']})

        context['document_content_json'] = json.dumps(doc.document_xml)

        serializer = WorkSerializer(context={'request': self.request}, many=True)
        works = Work.objects.filter(country=doc.country)
        context['works_json'] = json.dumps(serializer.to_representation(works))

        context['amendments_json'] = json.dumps(
            WorkAmendmentSerializer(context={'request': self.request}, many=True)
            .to_representation(doc.work.amendments))

        context['form'] = DocumentForm(instance=doc)
        context['countries'] = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in context['countries']})
        context['subtypes'] = Subtype.objects.order_by('name').all()
        context['languages'] = Language.objects.select_related('language').all()

        serializer = DocumentSerializer(context={'request': self.request}, many=True)
        context['documents_json'] = json.dumps(serializer.to_representation(DocumentViewSet.queryset.all()))
        return context


class UserProfileView(AbstractAuthedIndigoView, DetailView):
    queryset = User.objects
    context_object_name = 'user'
    template_name = 'indigo_app/user_profile/user_detail.html'


class EditAccountView(AbstractAuthedIndigoView, FormView):
    template_name = 'indigo_app/user_account/edit.html'
    form_class = UserForm

    def get_success_url(self):
        return reverse('edit_account')

    def get_form_kwargs(self):
        kwargs = super(EditAccountView, self).get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        return super(EditAccountView, self).form_valid(form)


class EditAccountAPIView(AbstractAuthedIndigoView, DetailView):
    context_object_name = 'user'
    template_name = 'indigo_app/user_account/api.html'

    def get_object(self):
        return self.request.user

    def post(self, request):
        request.user.editor.api_token().delete()
        # force a new one to be created
        request.user.editor.api_token()
        return self.get(request)
