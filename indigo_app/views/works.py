import json
import logging
from collections import Counter

from itertools import chain
from datetime import timedelta

from django import  forms
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.forms import formset_factory
from django.views.generic import DetailView, FormView, UpdateView, CreateView, DeleteView, View, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from reversion import revisions as reversion
import datetime

from cobalt import FrbrUri
from indigo.analysis.toc.base import descend_toc_pre_order, descend_toc_post_order
from indigo.plugins import plugins
from indigo_api.models import Subtype, Work, Amendment, Document, Task, PublicationDocument, \
    ArbitraryExpressionDate, Commencement, Workflow, Country, Locality
from indigo_api.serializers import WorkSerializer
from indigo_api.timeline import get_timeline
from indigo_api.views.attachments import view_attachment
from indigo_api.signals import work_changed
from indigo_app.revisions import decorate_versions
from indigo_app.forms import BatchCreateWorkForm, BatchUpdateWorkForm, ImportDocumentForm, WorkForm, CommencementForm, \
    NewCommencementForm, FindPubDocForm, RepealMadeBaseFormSet, AmendmentsBaseFormSet
from indigo_metrics.models import WorkMetrics

from .base import PlaceViewBase


log = logging.getLogger(__name__)


def publication_document_response(publication_document):
    """ Either return the publication document as a response, or redirect to the trusted URL.
    """
    if publication_document.trusted_url:
        return redirect(publication_document.trusted_url)
    return view_attachment(publication_document)


class WorkViewBase(PlaceViewBase, SingleObjectMixin):
    """ Base class for views based on a single work. This finds the work from
    the FRBR URI in the URL, and makes a `work` property available on the view.

    It also ensures that the place-lookup code picks up the place details from
    the FRBR URI.
    """
    model = Work
    context_object_name = 'work'
    # load work based on the frbr_uri
    pk_url_kwarg = None
    slug_url_kwarg = 'frbr_uri'
    slug_field = 'frbr_uri'
    permission_required = ('indigo_api.view_work',)

    def determine_place(self):
        if 'place' not in self.kwargs:
            # assume FRBR URI starts with `/akn`
            self.kwargs['place'] = self.kwargs['frbr_uri'].split('/')[2]

        return super(WorkViewBase, self).determine_place()

    def get_context_data(self, **kwargs):
        context = super(WorkViewBase, self).get_context_data(work=self.work, **kwargs)
        context['work_json'] = json.dumps(WorkSerializer(instance=self.work, context={'request': self.request}).data)
        return context

    def get_work_timeline(self, work):
        timeline = get_timeline(work)
        work_expressions = list(work.expressions().all())
        # add expressions
        for entry in timeline:
            entry.expressions = [e for e in work_expressions if e.expression_date == entry.date]
        return timeline

    def get_object(self, queryset=None):
        # the frbr_uri may include a portion, so we strip that here and update the kwargs
        try:
            frbr_uri = FrbrUri.parse(self.kwargs['frbr_uri'])
        except ValueError:
            raise Http404()

        self.kwargs['frbr_uri'] = frbr_uri.work_uri(False)
        self.frbr_uri = frbr_uri

        return super().get_object(queryset)

    @property
    def work(self):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return self.object


class WorkDependentView(WorkViewBase):
    """ Base for views that hang off a work URL, using the frbr_uri URL kwarg.

    Use this class instead of WorkViewBase if your view needs a different `model`,
    `slug_field`, etc.
    """
    _work = None

    @property
    def work(self):
        if not self._work:
            self._work = get_object_or_404(Work, frbr_uri=self.kwargs['frbr_uri'])
        return self._work


class EditWorkView(WorkViewBase, UpdateView):
    js_view = 'WorkDetailView'
    form_class = WorkForm
    prefix = 'work'
    permission_required = ('indigo_api.change_work',)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['country'] = self.country
        kwargs['locality'] = self.locality
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # save as a revision
        self.work.updated_by_user = self.request.user

        with reversion.create_revision():
            reversion.set_user(self.request.user)
            resp = super(EditWorkView, self).form_valid(form)

        # ensure any docs for this work at initial pub date move with it, if it changes
        if 'publication_date' in form.changed_data:
            old_date = form.initial['publication_date'] or self.work.commencement_date

            if old_date and self.work.publication_date:
                self.work.update_documents_at_publication_date(old_date, self.work.publication_date)

        # if the work title changes, ensure matching document titles do too
        if 'title' in form.changed_data:
            old_title = form.initial['title']
            if old_title:
                self.work.update_document_titles(old_title, self.work.title)

        if form.has_changed():
            # rename publication-document if frbr_uri has changed
            if 'frbr_uri' in form.changed_data:
                try:
                    self.work.publication_document.save()
                except PublicationDocument.DoesNotExist:
                    pass

            if 'country' in form.changed_data or 'locality' in form.changed_data:
                # update all tasks
                for task in self.work.tasks.all():
                    task.country = self.work.country
                    task.locality = self.work.locality
                    task.save()

            # signals
            work_changed.send(sender=self.__class__, work=self.work, request=self.request)
            messages.success(self.request, "Work updated.")

        return resp

    def get_success_url(self):
        return reverse('work', kwargs={'frbr_uri': self.work.frbr_uri})


class ApproveWorkView(WorkViewBase, View):
    permission_required = ('indigo_api.bulk_add_work',)
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        self.change_work_in_progress()
        url = reverse('work', kwargs={'frbr_uri': self.work.frbr_uri})
        if request.htmx:
            url = reverse('work_list_item', kwargs={'frbr_uri': self.work.frbr_uri})
        return redirect(url)

    def change_work_in_progress(self):
        work = self.get_object()
        user = self.request.user
        work.approve(user, self.request)


class UnapproveWorkView(ApproveWorkView):

    def change_work_in_progress(self):
        work = self.get_object()
        user = self.request.user
        work.unapprove(user)


class EditWorkModalView(EditWorkView):
    template_name = "indigo_api/_work_form_modal.html"


class EditWorkOffCanvasView(EditWorkView):
    template_name = "indigo_api/_work_form_content.html"

    def get_success_url(self):
        return reverse('work_edit_offcanvas', kwargs={'frbr_uri': self.work.frbr_uri})


class WorkListItemPartialView(WorkViewBase, TemplateView):
    template_name = "indigo_app/place/_work.html"


class AddWorkView(PlaceViewBase, CreateView):
    model = Work
    js_view = 'WorkDetailView'
    form_class = WorkForm
    prefix = 'work'
    permission_required = ('indigo_api.add_work',)
    is_create = True

    def get_form_kwargs(self):
        kwargs = super(AddWorkView, self).get_form_kwargs()

        work = Work()
        work.country = self.country
        work.locality = self.locality
        kwargs['instance'] = work
        kwargs['country'] = self.country
        kwargs['locality'] = self.locality

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(AddWorkView, self).get_context_data(**kwargs)

        work = {
            'country': self.country.code,
            'locality': self.locality.code if self.locality else None,
        }
        if self.country.publication_set.count() == 1:
            work['publication_name'] = self.country.publication_set.first().name
        context['work_json'] = json.dumps(work)

        context['subtypes'] = Subtype.objects.order_by('name').all()
        context['doctypes'] = self.doctypes()
        context['publication_date_optional'] = self.place.settings.publication_date_optional

        return context

    def form_valid(self, form):
        form.instance.updated_by_user = self.request.user
        form.instance.created_by_user = self.request.user

        with reversion.create_revision():
            reversion.set_user(self.request.user)
            return super(AddWorkView, self).form_valid(form)

    def get_success_url(self):
        return reverse('work', kwargs={'frbr_uri': self.object.frbr_uri})


class DeleteWorkView(WorkViewBase, DeleteView):
    permission_required = ('indigo_api.delete_work',)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.work.can_delete():
            self.work.delete()
            messages.success(request, 'Deleted %s · %s' % (self.work.title, self.work.frbr_uri))
            return redirect(self.get_success_url())
        else:
            messages.error(request, 'This work cannot be deleted while linked documents and related works exist.')
            return redirect('work_edit', frbr_uri=self.work.frbr_uri)

    def get_success_url(self):
        return reverse('place', kwargs={'place': self.kwargs['place']})


class WorkOverviewView(WorkViewBase, DetailView):
    js_view = ''
    template_name_suffix = '_overview'
    tab = 'overview'

    def get_context_data(self, **kwargs):
        context = super(WorkOverviewView, self).get_context_data(**kwargs)
        work_tasks = Task.objects.filter(work=self.work)

        context['active_tasks'] = work_tasks.exclude(state=Task.DONE)\
            .exclude(state=Task.CANCELLED)\
            .order_by('-created_at')
        context['work_timeline'] = self.get_work_timeline(self.work)
        context['contributors'] = self.get_top_contributors()

        # ensure work metrics are up to date
        WorkMetrics.create_or_update(self.work)

        return context

    def get_top_contributors(self):
        # count submitted tasks
        submitted = User.objects\
            .filter(submitted_tasks__work=self.work,
                    submitted_tasks__state=Task.DONE)\
            .annotate(task_count=Count(1))

        # count reviewed tasks
        reviewed = User.objects \
            .filter(reviewed_tasks__work=self.work,
                    reviewed_tasks__state=Task.DONE)\
            .annotate(task_count=Count(1))

        # merge them
        users = {u.id: u for u in chain(submitted, reviewed)}
        counter = Counter()
        counter.update({u.id: u.task_count for u in submitted})
        counter.update({u.id: u.task_count for u in reviewed})
        for user in users.values():
            user.task_count = counter[user.id]

        return sorted(users.values(), key=lambda u: -u.task_count)


class WorkCommencementsView(WorkViewBase, DetailView):
    template_name_suffix = '_commencements'
    tab = 'commencements'
    beautifier = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provisions = self.work.all_commenceable_provisions()
        context['commencements'] = commencements = self.work.commencements.all().reverse()
        context['has_all_provisions'] = any(c.all_provisions for c in commencements)
        context['has_main_commencement'] = any(c.main for c in commencements)
        context['uncommenced_provisions_count'] = len(self.work.all_uncommenced_provision_ids())
        context['total_provisions_count'] = sum(1 for _ in descend_toc_pre_order(provisions))
        context['everything_commenced'] = context['has_all_provisions'] or (provisions and not context['uncommenced_provisions_count'])

        self.beautifier = plugins.for_locale(
            'commencements-beautifier', self.country.code, None,
            self.locality.code if self.locality else None,
        )

        # decorate all provisions on the work
        commenced_provision_ids = [p_id for c in commencements for p_id in c.provisions]
        provisions = self.beautifier.decorate_provisions(provisions, commenced_provision_ids)
        context['provisions'] = provisions

        # decorate provisions on each commencement
        for commencement in commencements:
            commencement.rich_provisions = self.decorate_commencement_provisions(commencement, commencements)

        return context

    def decorate_commencement_provisions(self, commencement, commencements):
        # provisions from all documents up to this commencement's date
        provisions = self.work.all_commenceable_provisions(commencement.date)
        # provision ids commenced by everything else; will affect visibility per commencement form
        commenced_provision_ids = set(p_id for comm in commencements
                                      if comm != commencement
                                      for p_id in comm.provisions)

        # commencement status for displaying provisions on commencement detail
        rich_provisions = self.beautifier.decorate_provisions(provisions, commencement.provisions)

        # visibility for what to show in commencement form
        for p in descend_toc_post_order(rich_provisions):
            p.visible = p.id not in commenced_provision_ids
            p.visible_descendants = any(c.visible or c.visible_descendants for c in p.children)

        return rich_provisions


class WorkCommencementUpdateView(WorkDependentView, UpdateView):
    """ View to update or delete a commencement object.
    """
    http_method_names = ['post']
    model = Commencement
    pk_url_kwarg = 'commencement_id'
    form_class = CommencementForm

    def get_queryset(self):
        return self.work.commencements

    def get_permission_required(self):
        if 'delete' in self.request.POST:
            return ('indigo_api.delete_commencement',)
        return ('indigo_api.change_commencement',)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['work'] = self.work
        kwargs['provisions'] = list(descend_toc_pre_order(self.work.all_commenceable_provisions()))
        return kwargs

    def post(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            return self.delete(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object.updated_by_user = self.request.user
        super().form_valid(form)
        # make necessary changes to work, including updating updated_by_user
        self.object.rationalise(self.request.user)
        self.object.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        # send errors as messages, since we redirect back to the commencements page
        errors = list(form.non_field_errors())
        errors.extend([f'{fld}: ' + ', '.join(errs) for fld, errs in form.errors.items() if fld != '__all__'])
        messages.error(self.request, '; '.join(errors))
        return redirect(self.get_success_url())

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        work = self.object.commenced_work
        self.object.delete()
        work.updated_by_user = self.request.user
        work.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        url = reverse('work_commencements', kwargs={'frbr_uri': self.kwargs['frbr_uri']})
        if self.object.id:
            url += "#commencement-%s" % self.object.id
        return url


class WorkUncommencedView(WorkDependentView, View):
    """ Post-only view to mark a work as fully uncommenced.
    """
    http_method_names = ['post']
    permission_required = ('indigo_api.delete_commencement',)

    def post(self, request, *args, **kwargs):
        self.work.commenced = False
        self.work.updated_by_user = self.request.user
        self.work.save()

        for obj in self.work.commencements.all():
            obj.delete()

        return redirect('work_commencements', frbr_uri=self.kwargs['frbr_uri'])


class AddWorkCommencementView(WorkDependentView, CreateView):
    """ View to add a new commencement.
    """
    model = Commencement
    permission_required = ('indigo_api.add_commencement',)
    form_class = NewCommencementForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = Commencement(
            commenced_work=self.work,
            created_by_user=self.request.user,
            updated_by_user=self.request.user)
        return kwargs

    def form_valid(self, form):
        self.object = form.save()

        # useful defaults for new commencements
        if not self.work.commencements.filter(main=True).exists():
            self.object.main = True

        if not self.work.commencements.exists():
            self.object.all_provisions = True

        # make necessary changes to work, including updating updated_by_user
        self.object.rationalise(self.request.user)
        self.object.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return redirect(self.get_success_url())

    def get_success_url(self):
        url = reverse('work_commencements', kwargs={'frbr_uri': self.kwargs['frbr_uri']})
        if self.object and self.object.id:
            url = url + "#commencement-%s" % self.object.id
        return url


class WorkAmendmentsView(WorkViewBase, DetailView):
    template_name_suffix = '_amendments'
    tab = 'amendments'

    def get_context_data(self, **kwargs):
        context = super(WorkAmendmentsView, self).get_context_data(**kwargs)
        context['work_timeline'] = self.get_work_timeline(self.work)
        context['consolidation_date'] = self.work.as_at_date() or datetime.date.today()
        context['existing_consolidation_at_default_date'] = ArbitraryExpressionDate.objects.filter(work=self.work, date=context['consolidation_date']).exists()
        return context

    def get_work_timeline(self, work):
        # super method adds expressions to base work timeline
        timeline = super().get_work_timeline(work)
        for entry in timeline:
            # for creating and importing documents
            entry.create_import_document = entry.initial or any(
                e.type in ['amendment', 'consolidation'] for e in entry.events)

        return timeline


class WorkAmendmentDetailView(WorkDependentView, UpdateView):
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
        self.object.updated_by_user = self.request.user
        result = super().form_valid(form)
        self.object.amended_work.updated_by_user = self.request.user
        self.object.amended_work.save()

        # update old docs to have the new date as their expression date
        docs = Document.objects.filter(work=self.object.amended_work, expression_date=old_date)
        for doc in docs:
            doc.expression_date = self.object.date
            doc.updated_by_user = self.request.user
            doc.save()

        return result

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.can_delete():
            work = self.object.amended_work
            self.object.delete()
            work.updated_by_user = self.request.user
            work.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        url = reverse('work_amendments', kwargs={'frbr_uri': self.kwargs['frbr_uri']})
        if self.object.id:
            url += "#amendment-%s" % self.object.id
        return url


class AddWorkAmendmentView(WorkDependentView, CreateView):
    """ View to add a new amendment.
    """
    model = Amendment
    fields = ['date', 'amending_work']
    permission_required = ('indigo_api.add_amendment',)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = Amendment(amended_work=self.work)
        kwargs['instance'].created_by_user = self.request.user
        kwargs['instance'].updated_by_user = self.request.user
        return kwargs

    def form_valid(self, form):
        resp = super().form_valid(form)
        self.object.amended_work.updated_by_user = self.request.user
        self.object.amended_work.save()
        return resp

    def form_invalid(self, form):
        return redirect(self.get_success_url())

    def get_success_url(self):
        url = reverse('work_amendments', kwargs={'frbr_uri': self.kwargs['frbr_uri']})
        if self.object and self.object.id:
            url = url + "#amendment-%s" % self.object.id
        return url


class AddArbitraryExpressionDateView(WorkDependentView, CreateView):
    """ View to add a new arbitrary expression date.
    """
    model = ArbitraryExpressionDate
    fields = ['date']
    permission_required = ('indigo_api.add_amendment',)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = ArbitraryExpressionDate(work=self.work)
        kwargs['instance'].created_by_user = self.request.user
        return kwargs

    def form_valid(self, form):
        resp = super().form_valid(form)
        self.object.work.updated_by_user = self.request.user
        self.object.work.save()
        return resp

    def get_success_url(self):
        url = reverse('work_amendments', kwargs={'frbr_uri': self.kwargs['frbr_uri']})
        if self.object and self.object.id:
            url = url + "#arbitrary-expression-date-%s" % self.object.id
        return url


class EditArbitraryExpressionDateView(WorkDependentView, UpdateView):
    """ View to update or delete an arbitrary expression date.
    """
    http_method_names = ['post']
    model = ArbitraryExpressionDate
    pk_url_kwarg = 'arbitrary_expression_date_id'
    fields = ['date']

    def get_queryset(self):
        return self.work.arbitrary_expression_dates.all()

    def get_permission_required(self):
        if 'delete' in self.request.POST:
            return ('indigo_api.delete_amendment',)
        return ('indigo_api.change_amendment',)

    def post(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            return self.delete(request, *args, **kwargs)
        return super(EditArbitraryExpressionDateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        # get old/existing/incorrect date
        old_date = form.initial['date']

        # do normal things to amend work
        self.object.updated_by_user = self.request.user
        result = super().form_valid(form)
        self.object.work.updated_by_user = self.request.user
        self.object.work.save()

        # update old docs to have the new date as their expression date
        docs = Document.objects.filter(work=self.object.work, expression_date=old_date)
        for doc in docs:
            doc.expression_date = self.object.date
            doc.updated_by_user = self.request.user
            doc.save()

        return result

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.can_delete():
            work = self.object.work
            self.object.delete()
            work.updated_by_user = self.request.user
            work.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        url = reverse('work_amendments', kwargs={'frbr_uri': self.kwargs['frbr_uri']})
        if self.object and self.object.id:
            url = url + "#arbitrary-expression-date-%s" % self.object.id
        return url


class AddWorkPointInTimeView(WorkDependentView, CreateView):
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
            # create a new one with the current user as `created_by_user`
            doc = self.work.create_expression_at(self.request.user, date, language)

        return redirect('document', doc_id=doc.id)


class WorkRelatedView(WorkViewBase, DetailView):
    js_view = ''
    template_name_suffix = '_related'
    tab = 'related'

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
            'date': a.date,
        } for a in amended]
        context['amended'] = amended

        # amending works
        amended_by = Amendment.objects.filter(amended_work=self.work).prefetch_related('amending_work').order_by('amending_work__frbr_uri').all()
        amended_by = [{
            'rel': 'amended by',
            'work': a.amending_work,
            'date': a.date,
        } for a in amended_by]
        context['amended_by'] = amended_by

        # repeals
        repeals = []
        if self.work.repealed_by:
            repeals.append({
                'rel': 'repealed by',
                'work': self.work.repealed_by,
                'date': self.work.repealed_date,
            })
        repeals = repeals + [{
            'rel': 'repeals',
            'work': w,
            'date': w.repealed_date,
        } for w in self.work.repealed_works.all()]
        context['repeals'] = repeals

        return context


class WorkVersionsView(WorkViewBase, MultipleObjectMixin, DetailView):
    js_view = ''
    template_name_suffix = '_versions'
    object_list = None
    page_size = 20
    threshold = timedelta(seconds=3)
    tab = 'versions'

    def get_context_data(self, **kwargs):
        context = super(WorkVersionsView, self).get_context_data(**kwargs)

        actions = self.work.action_object_actions.all()
        amendment_actions = [aa for a in self.work.amendments.all() for aa in a.action_object_actions.all()]
        commencement_actions = [c for a in self.work.commencements.all() for c in a.action_object_actions.all()]
        versions = self.work.versions().defer('serialized_data').all()
        task_actions = self.get_task_actions()
        entries = sorted(chain(actions, amendment_actions, commencement_actions, versions, task_actions),
                         key=lambda x: x.revision.date_created if hasattr(x, 'revision') else x.timestamp,
                         reverse=True)
        entries = self.coalesce_entries(entries)

        decorate_versions([e for e in entries if hasattr(e, 'revision')])

        paginator, page, entries, is_paginated = self.paginate_queryset(entries, self.page_size)
        context.update({
            'paginator': paginator,
            'page': page,
            'is_paginated': is_paginated,
        })

        return context

    def coalesce_entries(self, items):
        """ If we have a "work updated" activity and a work revision within a few seconds of each other,
        don't show the "work updated" activity. The work revision is created first.

        Returns a new list of items. The items list must be in descending date order.
        """
        entries = []
        for i, entry in enumerate(items):
            # is this a revision?
            if i > 0 and getattr(entry, 'verb', None) == 'updated':
                prev = items[i - 1]
                if getattr(prev, 'revision', None) and prev.revision.date_created - entry.timestamp < self.threshold:
                    continue

            entries.append(entry)

        return entries

    def get_task_actions(self):
        tasks = self.work.tasks.all()
        actions_per_task = [t.action_object_actions.filter(verb='approved') for t in tasks]
        return [action for actions in actions_per_task for action in actions]


class WorkTasksView(WorkViewBase, DetailView):
    template_name_suffix = '_tasks'
    tab = 'tasks'

    def get_context_data(self, **kwargs):
        context = super(WorkTasksView, self).get_context_data(**kwargs)
        context['tasks'] = context['work'].tasks.all()
        context['task_groups'] = Task.task_columns(
            ['open', 'assigned', 'pending_review', 'done', 'cancelled'],
            context['tasks']
        )

        # warn when submitting task on behalf of another user
        Task.decorate_submission_message(context['tasks'], self)

        Task.decorate_potential_assignees(context['tasks'], self.country, self.request.user)
        Task.decorate_permissions(context['tasks'], self.request.user)

        return context


class RestoreWorkVersionView(WorkViewBase, DetailView):
    http_method_names = ['post']
    permission_required = ('indigo_api.change_work',)

    def post(self, request, frbr_uri, version_id):
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


class WorkPublicationDocumentView(WorkViewBase, View):
    def get(self, request, filename, *args, **kwargs):
        try:
            if self.work.publication_document.filename == filename:
                return publication_document_response(self.work.publication_document)
        except PublicationDocument.DoesNotExist:
            pass
        raise Http404()


class BatchAddWorkView(PlaceViewBase, FormView):
    template_name = 'indigo_api/work_batch_create.html'
    # permissions
    permission_required = ('indigo_api.bulk_add_work',)
    form_class = BatchCreateWorkForm

    _bulk_creator = None
    bulk_creator_kw = 'bulk-creator'
    bulk_creator_verb = 'Imported'

    @property
    def bulk_creator(self):
        if not self._bulk_creator:
            locality_code = self.locality.code if self.locality else None
            self._bulk_creator = plugins.for_locale(self.bulk_creator_kw, self.country.code, None, locality_code)
            self._bulk_creator.setup(self.country, self.locality, self.request)
        return self._bulk_creator

    def get_initial(self):
        return {
            'spreadsheet_url': self.place.settings.spreadsheet_url,
        }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['workflow'].queryset = Workflow.objects.filter(country=self.country, locality=self.locality, closed=False).order_by('title').all()

        url = form.data.get('spreadsheet_url') or form.initial['spreadsheet_url']

        def add_spreadsheet_url_error(error_message):
            """ Helper to let us add errors to the form before valid() has been called.
            """
            error = ValidationError(error_message)
            if 'spreadsheet_url' not in form.errors:
                form.errors['spreadsheet_url'] = form.error_class()
            form.errors['spreadsheet_url'].extend(error.error_list)

        if self.bulk_creator.is_gsheets_enabled and url:
            sheet_id = self.bulk_creator.gsheets_id_from_url(url)

            if not sheet_id:
                add_spreadsheet_url_error('Unable to get spreadsheet ID from URL')
            else:
                try:
                    sheets = self.bulk_creator.get_spreadsheet_sheets(sheet_id)
                    sheets = [s['properties']['title'] for s in sheets]
                    form.fields['sheet_name'].choices = [(s, s) for s in sheets]
                except ValueError:
                    add_spreadsheet_url_error(f"Unable to fetch spreadsheet information. Is your spreadsheet shared with {self.bulk_creator._gsheets_secret['client_email']}?")

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bulk_creator'] = self.bulk_creator

        # only show open tasks for each work
        rows = context.get('works') or []
        for row in rows:
            row.open_tasks = Task.objects.filter(work=row.work, state__in=Task.OPEN_STATES) if hasattr(row, 'work') else None

        return context

    def form_valid(self, form):
        error = None
        works = None
        dry_run = 'preview' in form.data

        if ('import' in form.data or 'preview' in form.data) and (
                # either no gsheets, or we have a sheet name
                not self.bulk_creator.is_gsheets_enabled or form.cleaned_data.get('sheet_name')):
            try:
                table = self.bulk_creator.get_datatable(
                    form.cleaned_data['spreadsheet_url'],
                    form.cleaned_data['sheet_name'])

                works = self.bulk_creator.create_works(table, dry_run, form.cleaned_data)
                if not dry_run:
                    messages.success(self.request, f"{self.bulk_creator_verb} {len([w for w in works if w.status == 'success'])} works.")
            except ValidationError as e:
                error = str(e)

        context_data = self.get_context_data(works=works, error=error, form=form, dry_run=dry_run)
        return self.render_to_response(context_data)


class BatchUpdateWorkView(BatchAddWorkView):
    template_name = 'indigo_api/work_batch_update.html'
    form_class = BatchUpdateWorkForm
    bulk_creator_kw = 'bulk-updater'
    bulk_creator_verb = 'Updated'


class ImportDocumentView(WorkViewBase, FormView):
    """ View to import a document as an expression for a work.

    This behaves a bit differently to normal form submission. The client
    submits the form via AJAX. If it's a success, we send them the location
    to go to. If not, we send them form errors.

    This gives a better experience than submitting the form natively, because
    it allows us to handle errors without refreshing the whole page.
    """
    template_name = 'indigo_api/work_import_document.html'
    permission_required = ('indigo_api.add_document',)
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
        document.created_by_user = self.request.user
        document.save()

        importer = plugins.for_document('importer', document)
        importer.section_number_position = opts.get('section_number_position', 'guess')

        importer.cropbox = opts.get('cropbox', None)
        importer.page_nums = form.cleaned_data['page_nums']

        try:
            importer.import_from_upload(upload, document, self.request)
        except ValueError as e:
            if document.pk:
                document.delete()
            log.error("Error during import: %s" % str(e), exc_info=e)
            return JsonResponse({'file': str(e) or "error during import"}, status=400)

        document.updated_by_user = self.request.user
        document.save_with_revision(self.request.user)

        return JsonResponse({'location': reverse('document', kwargs={'doc_id': document.id})})


class WorkPopupView(WorkViewBase, DetailView):
    template_name = 'indigo_api/work_popup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # is there a portion?
        if self.frbr_uri.portion:
            # get a document to use
            context["document"] = doc = (Document.objects
                .undeleted()
                .latest_expression()
                .filter(
                    work=self.work,
                    language=self.work.country.primary_language)
                .first()
            )
            if doc:
                portion = doc.doc.get_portion_element(self.frbr_uri.portion)
                if portion:
                    context["portion_html"] = doc.element_to_html(portion)

        return context


class PartialWorkFormView(PlaceViewBase, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # update the work object with the submitted form data
        context["work"] = work = Work(country=self.country, locality=self.locality, frbr_uri="/akn/za/act/2009/1")
        form = self.update_work(work)

        # use a fresh form based on the partially-updated work to re-render the template
        context["form"] = self.refreshed_form(form, work)

        return context

    def update_work(self, work):
        # update the object with the submitted form data, without saving the changes
        form = self.Form(self.request.GET, instance=work)
        form.is_valid()
        return form

    def refreshed_form(self, form, work):
        return self.Form(instance=work)


class WorkFormRepealView(PartialWorkFormView):
    """Just the repeal part of the work form to re-render the form when the user changes the repeal status
    through HTMX.
    """
    template_name = 'indigo_api/_work_repeal_form.html'

    class Form(forms.ModelForm):
        prefix = 'work'

        class Meta:
            model = Work
            fields = ('repealed_by', 'repealed_date')
            exclude = ('frbr_uri',)

    def update_work(self, work):
        form = super().update_work(work)
        if work.repealed_by:
            work.repealed_date = (work.repealed_by.commencement_date or
                                  work.repealed_by.publication_date)
        return form


class WorkFormParentView(PartialWorkFormView):
    """Just the parent part of the work form to re-render the form when the user changes the parent work through HTMX.
    """
    template_name = 'indigo_api/_work_parent_form.html'

    class Form(forms.ModelForm):
        prefix = 'work'

        class Meta:
            model = Work
            fields = ('parent_work',)


class WorkFormCommencementView(PartialWorkFormView):
    """Just the commencing work part of the work form to re-render the form when the user changes the commencing
     work through HTMX.
    """
    template_name = 'indigo_api/_work_commencement_form.html'

    class Form(forms.ModelForm):
        commencing_work = forms.ModelChoiceField(queryset=Work.objects, required=False)
        prefix = 'work'

        class Meta:
            model = Work
            fields = ('commencing_work',)

    def refreshed_form(self, form, work):
        return self.Form(initial={"commencing_work": form.cleaned_data["commencing_work"]}, instance=work)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["commencing_work"] = context["form"].initial["commencing_work"]
        return context


class FindPossibleDuplicatesView(PlaceViewBase, TemplateView):
    template_name = 'indigo_api/_work_possible_duplicates.html'

    class Form(WorkForm):
        prefix = 'work'

        class Meta:
            model = Work
            fields = ('title', 'frbr_uri', 'country', 'locality',)

        def find_actual_duplicate(self, pk):
            duplicate = Work.objects.filter(frbr_uri=self.instance.frbr_uri)
            duplicate = duplicate.exclude(pk=pk) if pk else duplicate
            return duplicate.first()

        def find_possible_duplicates(self, pk):
            # TODO: translations for keys
            qs = Work.objects.filter(country=self.country, locality=self.locality)
            qs = qs.exclude(pk=pk) if pk else qs
            possible_duplicates = {}

            # exact match on title
            match_title = qs.filter(title=self.cleaned_data.get('title'))
            if match_title:
                possible_duplicates['Match on title'] = match_title

            # match on date and number, e.g. BN 37 of 2002 and GN 37 of 2002
            frbr_date = self.cleaned_data.get('frbr_date')
            if frbr_date:
                # also match e.g. 2002-01-01 and 2002
                match_date = qs.filter(date__startswith=frbr_date[:4])
                match_date_and_number = match_date.filter(number=self.cleaned_data.get('frbr_number'))
                if match_date_and_number:
                    possible_duplicates['Match on year and number'] = match_date_and_number

            # match on Cap. number
            # TODO: match on other work properties per place too
            cap_number = self.cleaned_data.get('property_cap')
            if cap_number:
                match_cap_number = qs.filter(properties__contains={'cap': cap_number})
                if match_cap_number:
                    possible_duplicates['Match on Chapter number'] = match_cap_number

            return possible_duplicates

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.Form(self.country, self.locality, self.request.user, self.request.POST)
        form.full_clean()

        context["actual_duplicate"] = form.find_actual_duplicate(self.request.GET.get('pk'))
        context["possible_duplicates"] = form.find_possible_duplicates(self.request.GET.get('pk'))

        return context


class FindPublicationDocumentView(PlaceViewBase, TemplateView):
    template_name = 'indigo_api/_work_possible_publication_documents.html'

    class Form(forms.Form):
        publication_date = forms.DateField()
        publication_number = forms.CharField(required=False)
        publication_name = forms.CharField()
        prefix = 'work'

        class Meta:
            fields = ('publication_date', 'publication_number', 'publication_name')

        def find_possible_documents(self, country, locality):
            finder = plugins.for_locale('publications', country.code, None, locality.code if locality else None)
            if finder:
                try:
                    params = {
                        'date': self.cleaned_data.get('publication_date'),
                        'number': self.cleaned_data.get('publication_number'),
                        'publication': self.cleaned_data.get('publication_name'),
                        'country': country.code,
                        'locality': locality.code if locality else ''
                    }
                    return finder.find_publications(params)
                except (ValueError, ConnectionError):
                    return []

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.Form(self.request.POST)

        if form.is_valid():
            possible_documents = form.find_possible_documents(self.country, self.locality)
            if possible_documents:
                FindPubDocFormset = formset_factory(FindPubDocForm, extra=0)
                formset = FindPubDocFormset(prefix="pubdoc", initial=[
                    {
                        'name': doc.get('name'),
                        'trusted_url': doc.get('url'),
                        'size': doc.get('size'),
                        'mimetype': doc.get('mimetype')
                    }
                    for doc in possible_documents
                ])
                context["possible_doc_formset"] = formset
                context["frbr_uri"] = self.request.GET.get('frbr_uri')

        return context


class WorkFormPublicationDocumentView(PlaceViewBase, TemplateView):
    http_method_names = ['post', 'delete', 'get']
    template_name = 'indigo_api/_work_publication_document.html'

    class Form(forms.ModelForm):
        publication_document_file = forms.FileField(required=False)
        publication_document_trusted_url = forms.URLField(required=False, widget=forms.HiddenInput())
        publication_document_size = forms.IntegerField(required=False, widget=forms.HiddenInput())
        publication_document_mime_type = forms.CharField(required=False, widget=forms.HiddenInput())
        delete_publication_document = forms.CharField(required=False, widget=forms.HiddenInput())
        prefix = 'work'

        class Meta:
            model = Work
            fields = (
                'publication_document_trusted_url',
                'publication_document_size',
                'publication_document_mime_type',
                'delete_publication_document',
                'publication_document_file',
            )

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_id = self.request.GET.get('form')
        frbr_uri = self.request.GET.get('frbr_uri')
        if frbr_uri:
            work = Work.objects.filter(frbr_uri=frbr_uri).first()
            if work:
                context["work"] = work
        initial = {}
        if form_id:
            FindPubDocFormset = formset_factory(FindPubDocForm)
            formset = FindPubDocFormset(prefix="pubdoc", data=self.request.POST)
            if formset.is_valid():
                selected_form = formset.forms[int(form_id)]
                initial = {
                    'publication_document_trusted_url': selected_form.cleaned_data['trusted_url'],
                    'publication_document_size': selected_form.cleaned_data['size'],
                    'publication_document_mime_type': selected_form.cleaned_data['mimetype'],
                    'delete_publication_document': 'on',
                }

        if self.request.method == 'DELETE':
            initial['delete_publication_document'] = 'on'

        context["form"] = self.Form(initial=initial)
        return context


class WorkFormLocalityView(PlaceViewBase, TemplateView):
    http_method_names = ['post']
    template_name = 'indigo_api/_work_form_locality.html'

    class Form(forms.Form):
        country = forms.ModelChoiceField(queryset=Country.objects)
        locality = forms.ModelChoiceField(queryset=Locality.objects, required=False)
        prefix = 'work'

        class Meta:
            fields = ('country', 'locality')

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = form = self.Form(self.request.POST)
        if form.is_valid():
            form.fields['locality'].queryset = Locality.objects.filter(country=form.cleaned_data['country'])
        return context


class WorkFormRepealsMadeView(WorkViewBase, TemplateView):
    template_name = 'indigo_api/_work_form_repeals_made_form.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset = RepealMadeBaseFormSet(self.request.POST, prefix="repeals_made", form_kwargs={"work": self.work})
        initial = []
        if formset.is_valid():
            for form in formset.forms:
                delete = form.cleaned_data.get('DELETE')
                if delete and not form.is_repealed_work_saved():
                    continue

                initial.append({
                    'repealed_work': form.cleaned_data['repealed_work'],
                    'repealed_date': form.cleaned_data['repealed_date'],
                    'DELETE': delete,
                })

            repeal_made = self.request.POST.get('repeal_made')
            if repeal_made:
                repealed_work = Work.objects.filter(pk=repeal_made).first()
                if repealed_work and repealed_work.repealed_by != self.work and not any(
                        [True for i in initial if i["repealed_work"] == repealed_work]):
                    initial.append({
                        'repealed_work': repealed_work,
                        'repealed_date': repealed_work.repealed_date or self.work.commencement_date,
                    })

        context["form"] = {
           'repeals_made_formset': RepealMadeBaseFormSet(
               prefix='repeals_made',
               initial=initial,
               form_kwargs={"work": self.work}
           ),
        }
        context["work"] = self.work
        return context


class WorkFormAmendmentsView(WorkViewBase, TemplateView):
    template_name = 'indigo_api/_work_form_amendments_form.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        formset = AmendmentsBaseFormSet(self.request.POST, prefix="amendments", form_kwargs={"work": self.work})
        initial = []
        if formset.is_valid():
            for form in formset:
                delete = form.cleaned_data.get('DELETE')
                if delete:
                    if not Amendment.objects.filter(
                            amended_work=self.work,
                            amending_work=form.cleaned_data["amending_work"]
                    ).exists():
                        continue
                initial.append({
                    "amended_work": self.work,
                    "amending_work": form.cleaned_data["amending_work"],
                    "date": form.cleaned_data["date"],
                    "DELETE": form.cleaned_data["DELETE"],
                })
            amendment = self.request.POST.get("amendment")
            if amendment:
                amending_work = Work.objects.filter(pk=amendment).first()
                if amending_work:
                    # add amendment only if it does not exist and is not in the initial data
                    if not Amendment.objects.filter(amended_work=self.work, amending_work=amending_work).exists() and not any(
                            [True for i in initial if i["amending_work"] == amending_work]):

                        initial.append({
                            "amended_work": self.work,
                            "amending_work": amending_work,
                            "date": amending_work.commencement_date,
                        })

        context_data['form'] = {
            'amendments_formset': AmendmentsBaseFormSet(
                prefix="amendments",
                initial=initial,
                form_kwargs={"work": self.work}
            ),
        }
        return context_data

