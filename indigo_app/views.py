import json

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.views.generic import DetailView, TemplateView
from django.views.generic.list import MultipleObjectMixin
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect
from reversion import revisions as reversion

from cobalt.act import FrbrUri
from django.contrib.auth.models import User
from django.contrib.auth import get_user
from django.core.exceptions import ValidationError
from django.views.generic import FormView
from django.http import HttpRequest

from indigo_api.models import Document, Subtype, Work, Amendment
from indigo_api.serializers import DocumentSerializer, DocumentListSerializer, WorkSerializer, WorkAmendmentSerializer
from indigo_api.views.documents import DocumentViewSet
from indigo_api.signals import work_changed
from indigo_app.models import Language, Country
from indigo_app.revisions import decorate_versions

from .forms import DocumentForm, BatchCreateWorkForm


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

        serializer = DocumentListSerializer(context={'request': self.request})
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
    template_name = 'work/new_batch.html'
    # permissions
    permission_required = ('indigo_api.add_work',)
    form_class = BatchCreateWorkForm

    def form_valid(self, form):
        def get_works(table):

            works = []

            for idx, row in enumerate(table):
                # TODO: match header row contents rather than using column numbers
                row_number = idx+1

                info = {
                    'row': row_number,
                }

                frbr_uri = get_frbr_uri(row)

                # TODO: fix get_uri to return uri as false if validation error?

                if frbr_uri:

                    try:
                        work = Work.objects.get(frbr_uri=frbr_uri)
                        info['work'] = work
                        info['status'] = 2

                    # TODO one day: also mark another work as duplicate if user is trying to import two of the same (currently only the second one will be '2')

                    except Work.DoesNotExist:

                        work = Work()

                        work.frbr_uri = frbr_uri
                        work.title = row[8]
                        work.country = row[9]
                        work.publication_name = row[10]
                        work.publication_number = row[11]
                        work.publication_date = row[12]
                        work.commencement_date = row[13]
                        work.assent_date = row[14]
                        # work.created_by_user = gett_user()
                        # work.updated_by_user = gett_user()

                        info['work'] = work

                        try:
                            work.save()
                            info['status'] = 1

                        except ValidationError as e:
                            info['status'] = 3
                            info['error_message'] = e.message

                works.append(info)

            return works

        def get_table(spreadsheet_url):
            # get list of lists where each inner list is a row in a spreadsheet
            # use gspread
            # TODO: unfake get_table()
            # fake table!
            return [
                ['ZA', 'WC011', 'Act', 'By-law', '', '', 'liquor-trading-hours', '', 'By-law on liquor trading days and hours of Matzikama Municipality', 'ZA', 'Western Cape Provincial Gazette', '7339', '2014-12-12', '2014-12-12', '', '', '2018-06-01', '', ''],
                ['ZA', '', 'Act', '', '', 'xyz', 'liquor', '', 'By-law on liquor trading', 'ZA', 'Gazette', '7339', '2014-12-12', '2014-12-12', '', '', '2018-06-01', '', ''],
                ['ZA', '', 'Act', '', '', '2014', '6', '', 'The Cake Act', 'ZA', 'National Gazette', '40125', '2016-03-17', '', '', '', '', '', ''],
            ]

        def get_frbr_uri(row):
            # TODO: also make less brittle (check header row instead)
            # TODO one day: generate 'number' based on title if number isn't an int (replace spaces with dashes, lowercase, delete to, of, for, etc)
            country = row[0].lower()
            locality = row[1].lower()
            doctype = row[2].lower()
            subtype = row[3].lower()
            actor = row[4].lower()
            date = row[5]
            number = row[6].lower()

            try:
                frbr_uri = FrbrUri(country=country, locality=locality, doctype=doctype, subtype=subtype, actor=actor, date=date, number=number)
                return frbr_uri.work_uri()

            except ValidationError as e:
                return 'frbr uri message:', e.message

        # def gett_user():
        # spoiler: this doesn't work
        #     request = HttpRequest()
            # TODO: get current user
            # return get_user(request)

        table = get_table(form.cleaned_data['spreadsheet_url'])
        works = get_works(table)
        return self.render_to_response(self.get_context_data(works=works))


""" each work should have this dict structure:
        works = [
            {
                'row': 1,
                'title': 'Hello',
                'status': 3,                    # failure - duplicate
                'frbr_uri': '/za/act/2016/4',   # shouldn't link in html
            },
            {
                'row': 2,
                'title': 'Hi again',
                'status': 1,                    # sucess
                'frbr_uri': '/za/act/2016/5',   # _should_ link in html
            },
            {
                'row': 3,
                'title': 'One more',
                'status': 2,                    # failure - general
                'frbr_uri': '/za/act/2017/-',   # shouldn't link in html
            },
        ]
"""




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

        serializer = DocumentListSerializer(context={'request': self.request})
        context['documents_json'] = json.dumps(serializer.to_representation(DocumentViewSet.queryset.all()))

        return context
