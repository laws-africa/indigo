import json
import logging
from collections import Counter

from itertools import chain, groupby
from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.forms import formset_factory
from django.views.generic import DetailView, FormView, UpdateView, CreateView, DeleteView, View, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin
from django_htmx.http import HttpResponseClientRedirect
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext as __
from django.shortcuts import redirect, get_object_or_404
from reversion import revisions as reversion
import datetime

from cobalt import FrbrUri
from indigo.analysis.toc.base import descend_toc_pre_order, descend_toc_post_order
from indigo.plugins import plugins
from indigo_api.models import Work, Amendment, Document, Task, PublicationDocument, ArbitraryExpressionDate, \
    Commencement, Country, Locality, TaxonomyTopic
from indigo_api.serializers import WorkSerializer
from indigo_api.timeline import get_timeline, TimelineEntry
from indigo_api.views.attachments import view_attachment
from indigo_api.signals import work_changed
from indigo_app.revisions import decorate_versions
from indigo_app.views.places import get_work_overview_data
from indigo_app.forms import BatchCreateWorkForm, BatchUpdateWorkForm, ImportDocumentForm, WorkForm, CommencementForm, \
    FindPubDocForm, RepealMadeBaseFormSet, AmendmentsBaseFormSet, CommencementsMadeBaseFormset, \
    ConsolidationsBaseFormset, CommencementsBaseFormset, WorkChapterNumbersFormSet

from .base import PlaceViewBase, AbstractAuthedIndigoView

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
    add_work_json_context = True

    def determine_place(self):
        if 'place' not in self.kwargs:
            # check that self.kwargs['frbr_uri'] is in fact an FRBR URI first
            try:
                frbr_uri = FrbrUri.parse(self.kwargs['frbr_uri'])
                self.kwargs['place'] = frbr_uri.place
            except ValueError as e:
                raise Http404(e)

        super().determine_place()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(work=self.work, **kwargs)
        if self.add_work_json_context:
            # TODO: WorkSerializer should only have important information that views use; taxonomy topics should be removed
            context['work_json'] = json.dumps(WorkSerializer(instance=self.work, context={'request': self.request}).data)
        return context

    def get_work_timeline(self, work):
        timeline = get_timeline(work)
        work_expressions = work.expressions().all()
        # add expressions
        for entry in timeline:
            entry.expressions = [e for e in work_expressions if e.expression_date == entry.date]
        # add tasks
        timeline_tasks = work.tasks.filter(timeline_date__isnull=False).exclude(state=Task.CANCELLED)
        dates = [entry.date for entry in timeline]
        simple_tasks = list(timeline_tasks.filter(timeline_date__in=dates))
        # simple case: add tasks to existing corresponding entries
        for entry in timeline:
            entry.tasks = [t for t in simple_tasks if t.timeline_date == entry.date]

        # these will have their own entries as their dates aren't in the timeline yet
        extra_tasks = timeline_tasks.exclude(timeline_date__in=dates).order_by('timeline_date')
        extra_documents = work_expressions.exclude(expression_date__in=dates).order_by('expression_date')
        for date, tasks in groupby(extra_tasks, key=lambda t: t.timeline_date):
            entry = TimelineEntry(date=date, initial=False, events=[])
            entry.tasks = list(tasks)
            entry.stranded_documents = list(extra_documents.filter(expression_date=date))
            timeline, dates = self.insert_entry(timeline, dates, entry)

        extra_documents = extra_documents.exclude(expression_date__in=dates).order_by('expression_date')
        for date, documents in groupby(extra_documents, key=lambda d: d.expression_date):
            entry = TimelineEntry(date=date, initial=False, events=[])
            entry.stranded_documents = list(documents)
            timeline, dates = self.insert_entry(timeline, dates, entry)

        return timeline

    def insert_entry(self, timeline, dates, entry):
        # dates are in descending order, so slot the entry in before the first one that's earlier
        for i, date in enumerate(dates):
            if date < entry.date:
                timeline.insert(i, entry)
                dates.insert(i, entry.date)
                break
        if entry.date not in dates:
            # we've gone past the earliest / last one, so just append
            timeline.append(entry)
            dates.append(entry.date)

        return timeline, dates

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
    form_class = WorkForm
    prefix = 'work'
    permission_required = ('indigo_api.change_work',)
    add_work_json_context = False

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
            messages.success(self.request, _("Work updated."))

        return resp

    def get_success_url(self):
        return reverse('work', kwargs={'frbr_uri': self.work.frbr_uri})


class EditWorkOffCanvasView(EditWorkView):
    template_name = "indigo_api/_work_form_offcanvas_body.html"

    def render_to_response(self, context, **response_kwargs):
        resp = super().render_to_response(context, **response_kwargs)
        # when a work is created off-canvas, it redirects to this view, which doesn't give it a chance to tell
        # the browser to refresh the work list. Instead, AddWorkOffCanvasView sets a query param to tell us to
        # trigger the refresh.
        if self.request.GET.get('hx-trigger'):
            resp.headers['HX-Trigger'] = "hx_refresh_work_list"
        return resp

    def get_success_url(self):
        return reverse('work_edit_offcanvas', kwargs={'frbr_uri': self.work.frbr_uri})


class UnapproveWorkView(WorkViewBase, View):
    def post(self, request, *args, **kwargs):
        work = self.get_object()
        work.unapprove(self.request.user)
        url = reverse('work', kwargs={'frbr_uri': self.work.frbr_uri})
        if request.htmx:
            url = reverse('work_list_item', kwargs={'frbr_uri': self.work.frbr_uri})
        return redirect(url)


class WorkListItemPartialView(WorkViewBase, TemplateView):
    template_name = "indigo_app/place/_work.html"


class AddWorkView(PlaceViewBase, CreateView):
    model = Work
    form_class = WorkForm
    prefix = 'work'
    permission_required = ('indigo_api.add_work',)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['country'] = self.country
        kwargs['locality'] = self.locality
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        # allow pre-population of fields by passing in request params
        initial = dict(self.request.GET)
        initial.update({
            'country': self.country,
            'locality': self.locality,
        })
        return initial

    def get_context_data(self, **kwargs):
        context = super(AddWorkView, self).get_context_data(**kwargs)

        work = {
            'country': self.country.code,
            'locality': self.locality.code if self.locality else None,
        }
        if self.country.publication_set.count() == 1:
            work['publication_name'] = self.country.publication_set.first().name
        context['work_json'] = json.dumps(work)
        context['publication_date_optional'] = self.place.settings.publication_date_optional

        return context

    def form_valid(self, form):
        form.instance.country = self.country
        form.instance.locality = self.locality
        form.instance.updated_by_user = self.request.user
        form.instance.created_by_user = self.request.user

        with reversion.create_revision():
            reversion.set_user(self.request.user)
            return super(AddWorkView, self).form_valid(form)

    def get_success_url(self):
        return reverse('work', kwargs={'frbr_uri': self.object.frbr_uri})


class AddWorkOffCanvasView(AddWorkView):
    template_name = "indigo_api/_work_form_offcanvas_body.html"

    def get_success_url(self):
        return reverse('work_edit_offcanvas', kwargs={'frbr_uri': self.object.frbr_uri}) + "?hx-trigger=hx_refresh_work_list"


class DeleteWorkView(WorkViewBase, DeleteView):
    permission_required = ('indigo_api.delete_work',)

    def form_valid(self, form):
        self.object = self.get_object()

        if self.work.can_delete():
            self.work.delete()
            messages.success(self.request, _('Deleted %(title)s · %(frbr_uri)s') % {"title": self.work.title, "frbr_uri": self.work.frbr_uri})
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, _('This work cannot be deleted while linked documents and related works exist.'))
            return redirect('work_edit', frbr_uri=self.work.frbr_uri)

    def get_success_url(self):
        return reverse('place', kwargs={'place': self.kwargs['place']})


class WorkOverviewView(WorkViewBase, DetailView):
    js_view = ''
    template_name_suffix = '_overview'
    tab = 'overview'
    add_work_json_context = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['overview_data'] = get_work_overview_data(self.work)
        context['active_tasks'] = self.work.tasks.filter(state__in=Task.OPEN_STATES).order_by('-created_at')
        context['work_timeline'] = self.get_work_timeline(self.work)
        context['contributors'] = self.get_top_contributors()
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


class WorkCommentsView(WorkViewBase, DetailView):
    """HTMX view to render updated work comments"""
    template_name = 'indigo_api/_work_comments.html'


class WorkCommencementsView(WorkViewBase, DetailView):
    template_name_suffix = '_commencements'
    tab = 'commencements'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['commencements'] = self.work.commencements.all().reverse()
        context['has_uncommenced_provisions'] = self.work.all_uncommenced_provision_ids(return_bool=True)
        context['blank_commencement_exists'] = self.work.commencements.filter(date=None, commencing_work=None).exists()
        return context


class WorkUncommencedProvisionsDetailView(WorkViewBase, DetailView):
    template_name = 'indigo_api/commencements/_work_uncommenced_provisions_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: only get all_uncommenced_provision_ids once? decorate_work_provisions() gets all_commenceable_provisions again
        context['uncommenced_provisions_count'] = len(self.work.all_uncommenced_provision_ids())
        # only decorate provisions if there are uncommenced provisions
        if context['uncommenced_provisions_count']:
            context['provisions'] = self.decorate_work_provisions()
        return context

    def decorate_work_provisions(self):
        beautifier = plugins.for_locale(
            'commencements-beautifier', self.work.country.code, None,
            self.work.locality.code if self.work.locality else None,
        )
        commencements = self.work.commencements.all().reverse()
        # TODO: avoid calling this again?
        provisions = self.work.all_commenceable_provisions()
        commenced_provision_ids = [p_id for c in commencements for p_id in c.provisions]
        return beautifier.decorate_provisions(provisions, commenced_provision_ids)


class WorkCommencementDetailView(AbstractAuthedIndigoView, DetailView):
    http_method_names = ['post', 'get']
    model = Commencement

    def get_permission_required(self):
        if 'delete' in self.request.POST:
            return ('indigo_api.delete_commencement',)
        return ('indigo_api.view_commencement',)

    def post(self, request, *args, **kwargs):
        # for now, the only thing we post to this view is 'delete'
        if 'delete' in request.POST:
            return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        commencement = self.get_object()
        work = commencement.commenced_work
        commencement.delete()
        work.updated_by_user = self.request.user
        work.save()
        return redirect(reverse('work_commencements', kwargs={'frbr_uri': work.frbr_uri}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['work'] = self.object.commenced_work
        return context


class WorkCommencementProvisionsDetailView(AbstractAuthedIndigoView, DetailView):
    model = Commencement
    template_name = 'indigo_api/commencements/_commencement_provisions_detail.html'
    permission_required = ('indigo_api.view_commencement',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['commencement'].rich_provisions = self.decorate_commencement_provisions(context['commencement'], date=self.get_date(context))
        return context

    def get_date(self, context):
        # just use the commencement's date (the default if no date is specified) for the read-only view
        return None

    def decorate_commencement_provisions(self, commencement, date=None):
        date = date or commencement.date
        beautifier = plugins.for_locale(
            'commencements-beautifier', commencement.commenced_work.country.code, None,
            commencement.commenced_work.locality.code if commencement.commenced_work.locality else None,
        )
        # provisions from all documents up to the commencement's date
        # (expensive but needs to be worked out for each commencement)
        # TODO: get provisions from a form instead?
        provisions = commencement.commenced_work.all_commenceable_provisions(date)
        # provisions commenced by everything else
        other_commencements = commencement.commenced_work.commencements.exclude(pk=commencement.pk)
        commenced_provision_ids = set(p_id for comm in other_commencements for p_id in comm.provisions)
        # commencement status for displaying provisions on commencement detail
        rich_provisions = beautifier.decorate_provisions(provisions, commencement.provisions)
        # disable already-commenced provisions in the commencement form
        for p in descend_toc_post_order(rich_provisions):
            p.disabled = p.id in commenced_provision_ids

        return rich_provisions


class WorkCommencementEditView(WorkDependentView, UpdateView):
    http_method_names = ['get', 'post']
    model = Commencement
    pk_url_kwarg = 'pk'
    form_class = CommencementForm
    context_object_name = 'commencement'
    permission_required = ('indigo_api.change_commencement',)
    add_work_json_context = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disable_main_commencement'] = self.work.main_commencement and not self.object.main
        context['disable_all_provisions'] = self.work.commencements.count() > 1
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['work'] = self.work
        # TODO: include date here, use again later?
        kwargs['provisions'] = list(descend_toc_pre_order(self.work.all_commenceable_provisions()))
        return kwargs

    def form_valid(self, form):
        self.object.updated_by_user = self.request.user
        self.object = form.save()
        return HttpResponseClientRedirect(redirect_to=self.get_success_url())

    def get_success_url(self):
        # re-render the whole page (updated provisions)
        # TODO: navigate to the commencement on the page, e.g. works/…/commencements/#commencement-1076
        return reverse('work_commencements', kwargs={'frbr_uri': self.work.frbr_uri})


class WorkCommencementCommencingWorkEditView(WorkCommencementEditView):
    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class WorkCommencementProvisionsEditView(WorkCommencementProvisionsDetailView, FormView):
    template_name = 'indigo_api/commencements/_commencement_provisions_edit.html'
    permission_required = ('indigo_api.change_commencement',)
    form_class = CommencementForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['work'] = self.work
        # TODO: include date here, use again later?
        kwargs['provisions'] = list(descend_toc_pre_order(kwargs['work'].all_commenceable_provisions()))
        return kwargs

    def get_date(self, context):
        # get the currently selected date from the form -- different provisions may be available
        form = context['form']
        form.is_valid()
        return form.cleaned_data.get('date')

    def get_success_url(self):
        return reverse('work_commencement_edit', kwargs={'frbr_uri': self.work.frbr_uri, 'pk': self.object.id})

    @property
    def work(self):
        # TODO: rather inherit from something else (WorkDependentView?) -- figure out inheritance order
        return Work.objects.get(frbr_uri=self.kwargs['frbr_uri'])

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class WorkCommencementAddView(WorkDependentView, CreateView):
    model = Commencement
    pk_url_kwarg = 'pk'
    form_class = CommencementForm
    context_object_name = 'commencement'
    permission_required = ('indigo_api.add_commencement',)
    add_work_json_context = False

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["work"] = self.work
        return kwargs

    def form_valid(self, form):
        form.instance.commenced_work = self.work
        form.instance.created_by_user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, __("Couldn't add another blank commencement"))
        return HttpResponseClientRedirect(redirect_to=reverse('work_commencements', kwargs={'frbr_uri': self.work.frbr_uri}))

    def get_success_url(self):
        return reverse('work_commencement_edit', kwargs={'frbr_uri': self.work.frbr_uri, 'pk': self.object.id})


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


class WorkAmendmentsView(WorkViewBase, DetailView):
    template_name_suffix = '_amendments'
    tab = 'amendments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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


class WorkAmendmentUpdateView(WorkDependentView, UpdateView):
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
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # do normal things to amend work
        self.object.updated_by_user = self.request.user
        result = super().form_valid(form)
        self.object.amended_work.updated_by_user = self.request.user
        self.object.amended_work.save()
        # update documents and tasks
        self.object.update_date_for_related(old_date=form.initial['date'])

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


class WorkAmendmentDropdownView(WorkDependentView, DetailView):
    model = Amendment
    pk_url_kwarg = 'amendment_id'
    template_name = 'indigo_api/timeline/_amendment_dropdown.html'
    context_object_name = 'amendment'

    def get_queryset(self):
        return self.work.amendments


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
        context = super().get_context_data(**kwargs)
        context['tasks'] = Task.objects.filter(work=context['work']).all()
        context['task_groups'] = Task.task_columns(
            ['open', 'assigned', 'pending_review', 'done', 'cancelled'],
            context['tasks']
        )

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
            reversion.set_comment(_("Restored version %(version_id)s") % {"version_id": version.id})
            version.revert()
        messages.success(request, _('Restored version %(version_id)s') % {"version_id": version.id})

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
                add_spreadsheet_url_error(_('Unable to get spreadsheet ID from URL'))
            else:
                try:
                    sheets = self.bulk_creator.get_spreadsheet_sheets(sheet_id)
                    sheets = [s['properties']['title'] for s in sheets]
                    form.fields['sheet_name'].choices = [(s, s) for s in sheets]
                except ValueError:
                    add_spreadsheet_url_error(_("Unable to fetch spreadsheet information. Is your spreadsheet shared with %(email)s?") % {"email": self.bulk_creator._gsheets_secret['client_email']})

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bulk_creator'] = self.bulk_creator

        # only show open tasks for each work
        rows = context.get('works') or []
        for row in rows:
            if hasattr(row, 'work') and row.work.pk:
                row.open_tasks = Task.objects.filter(work=row.work, state__in=Task.OPEN_STATES)

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
            log.error(_("Error during import: %(error)s") % {"error": str(e)}, exc_info=e)
            return JsonResponse({'file': str(e) or "error during import"}, status=400)

        document.updated_by_user = self.request.user
        document.save_with_revision(self.request.user)

        return JsonResponse({'location': reverse('document', kwargs={'doc_id': document.id})})


class WorkPopupView(WorkViewBase, DetailView):
    template_name = 'indigo_api/work_popup.html'
    add_work_json_context = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['overview_data'] = get_work_overview_data(self.work)

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
            fields = ('repealed_by', 'repealed_date', 'repealed_verb', 'repealed_note')
            exclude = ('frbr_uri',)

        repealed_verb = forms.ChoiceField(required=False, choices=Work.REPEALED_VERB_CHOICES)

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
            keys_choices = {
                'match_on_title': _('Match on title'),
                'match_on_date_number': _('Match on year and number'),
            }
            qs = Work.objects.filter(country=self.country, locality=self.locality)
            qs = qs.exclude(pk=pk) if pk else qs
            possible_duplicates = {}

            # exact match on title
            match_title = qs.filter(title=self.cleaned_data.get('title'))
            if match_title:
                possible_duplicates[keys_choices['match_on_title']] = match_title

            # match on date and number, e.g. BN 37 of 2002 and GN 37 of 2002
            frbr_date = self.cleaned_data.get('frbr_date')
            if frbr_date:
                # also match e.g. 2002-01-01 and 2002
                match_date = qs.filter(date__startswith=frbr_date[:4])
                match_date_and_number = match_date.filter(number=self.cleaned_data.get('frbr_number'))
                if match_date_and_number:
                    possible_duplicates[keys_choices['match_on_date_number']] = match_date_and_number

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
        publication_name = forms.CharField(required=False)
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
        formset = RepealMadeBaseFormSet(self.request.POST,
                                        user=self.request.user,
                                        work=self.work,
                                        prefix="repeals_made",
                                        form_kwargs={"work": self.work,
                                                     "user": self.request.user})
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
               user=self.request.user,
               work=self.work,
               prefix='repeals_made',
               initial=initial,
               form_kwargs={"work": self.work,
                            "user": self.request.user}
           ),
        }
        context["work"] = self.work
        return context


class WorkFormChapterNumbersView(WorkViewBase, TemplateView):
    template_name = 'indigo_api/_work_form_chapter_numbers_form.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        formset = WorkChapterNumbersFormSet(self.request.POST,
                                            user=self.request.user,
                                            work=self.work,
                                            prefix='chapter_numbers',
                                            form_kwargs={"work": self.work,
                                                         "user": self.request.user})
        if not formset.is_valid():
            context_data['formset'] = formset
        else:
            initial = [form.cleaned_data for form in formset
                       # skip empty extra and deleted unsaved forms
                       if form.cleaned_data and not
                       (form.cleaned_data.get('DELETE') and not form.cleaned_data.get('id'))]
            context_data['formset'] = WorkChapterNumbersFormSet(
                user=self.request.user,
                work=self.work,
                prefix='chapter_numbers',
                initial=initial,
                form_kwargs={"work": self.work,
                             "user": self.request.user}
            )
        return context_data


class WorkFormAmendmentsView(WorkViewBase, TemplateView):
    template_name = 'indigo_api/_work_form_amendments_form.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        amended_by = self.request.POST.get("amended_by")
        amendments_made = self.request.POST.get("amendments_made")
        deleting = self.request.GET.get("delete")
        amendment_work_id = None
        prefix = None

        if amended_by:
            amendment_work_id = amended_by
            prefix = "amended_by"
        elif amendments_made:
            amendment_work_id = amendments_made
            prefix = "amendments_made"
        elif deleting:
            prefix = deleting

        context_data = super().get_context_data(**kwargs)
        formset = AmendmentsBaseFormSet(self.request.POST,
                                        user=self.request.user,
                                        work=self.work,
                                        prefix=prefix,
                                        form_kwargs={"work": self.work,
                                                     "user": self.request.user})
        initial = []
        if formset.is_valid():
            for form in formset:
                delete = form.cleaned_data.get('DELETE')
                if delete:
                    if not form.cleaned_data.get('id'):
                        continue
                initial.append({
                    "amended_work": form.cleaned_data["amended_work"],
                    "amending_work": form.cleaned_data["amending_work"],
                    "date": form.cleaned_data["date"],
                    "id": form.cleaned_data["id"],
                    "DELETE": form.cleaned_data["DELETE"],
                })
            if amendment_work_id:
                amending_works = {form.cleaned_data["amending_work"] for form in formset}
                amended_works = {form.cleaned_data["amended_work"] for form in formset}
                work = Work.objects.filter(pk=amendment_work_id).first()
                if work:
                    if prefix == "amended_by":
                        initial.append({
                            "amended_work": self.work,
                            "amending_work": work,
                            "date": work.commencement_date if work not in amending_works else None,
                        })
                    elif prefix == "amendments_made":
                        initial.append({
                            "amended_work": work,
                            "amending_work": self.work,
                            "date": self.work.commencement_date if work not in amended_works else None,
                        })

        else:
            context_data['formset'] = formset
            context_data["prefix"] = prefix

            return context_data

        context_data['formset'] = AmendmentsBaseFormSet(
                user=self.request.user,
                work=self.work,
                prefix=prefix,
                initial=initial,
                form_kwargs={"work": self.work,
                             "user": self.request.user}
            )
        context_data["prefix"] = prefix
        return context_data


class WorkFormCommencementsView(WorkViewBase, TemplateView):
    template_name = 'indigo_api/_work_form_commencements_form.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["prefix"] = prefix = "commencements"
        adding = self.request.GET.get("add") is not None
        formset = CommencementsBaseFormset(self.request.POST,
                                           prefix=prefix,
                                           form_kwargs={"work": self.work,
                                                        "user": self.request.user})
        if not formset.is_valid():
            # re-render the busted formset
            context_data["formset"] = formset
            return context_data

        initial = [{
            "commenced_work": form.cleaned_data["commenced_work"],
            "commencing_work": form.cleaned_data["commencing_work"],
            "note": form.cleaned_data["note"],
            "date": form.cleaned_data["date"],
            "id": form.cleaned_data["id"],
            "DELETE": form.cleaned_data["DELETE"],
            "clear_commencing_work": form.cleaned_data["clear_commencing_work"],
        } for form in formset]

        if adding:
            # add a blank one
            blank_kwargs = {"commenced_work": self.work}
            # use the publication date if it's the first one being added
            if not initial:
                blank_kwargs['date'] = self.work.publication_date
            initial.append(blank_kwargs)

        context_data["formset"] = CommencementsBaseFormset(
            prefix=prefix,
            initial=initial,
            form_kwargs={"work": self.work,
                         "user": self.request.user}
        )

        return context_data


class WorkFormCommencementsMadeView(WorkViewBase, TemplateView):
    template_name = 'indigo_api/_work_form_commencements_made_form.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        commencement_made = self.request.POST.get("commencements_made")
        deleting = self.request.GET.get("delete")
        commencement_work_id = None
        prefix = None

        if commencement_made:
            commencement_work_id = commencement_made
            prefix = "commencements_made"
        elif deleting:
            prefix = deleting

        context_data = super().get_context_data(**kwargs)
        formset = CommencementsMadeBaseFormset(self.request.POST,
                                               user=self.request.user,
                                               work=self.work,
                                               prefix=prefix,
                                               form_kwargs={"work": self.work,
                                                            "user": self.request.user})
        initial = []
        if formset.is_valid():
            for form in formset:
                delete = form.cleaned_data.get('DELETE')
                if delete:
                    if not form.cleaned_data.get('id'):
                        continue
                initial.append({
                    "commenced_work": form.cleaned_data["commenced_work"],
                    "commencing_work": form.cleaned_data["commencing_work"],
                    "note": form.cleaned_data["note"],
                    "date": form.cleaned_data["date"],
                    "id": form.cleaned_data["id"],
                    "DELETE": form.cleaned_data["DELETE"],
                })
            if commencement_work_id:
                commenced_works = {form.cleaned_data["commenced_work"] for form in formset}
                work = Work.objects.filter(pk=commencement_work_id).first()
                if work:
                    if prefix == "commencements_made":
                        initial.append({
                            "commenced_work": work,
                            "commencing_work": self.work,
                            "date": self.work.commencement_date if work not in commenced_works else None,
                        })

        else:
            context_data['formset'] = formset
            context_data["prefix"] = prefix

            return context_data

        context_data['formset'] = CommencementsMadeBaseFormset(
            user=self.request.user,
            work=self.work,
            prefix=prefix,
            initial=initial,
            form_kwargs={"work": self.work,
                         "user": self.request.user}
        )
        context_data["prefix"] = prefix
        return context_data


class WorkFormConsolidationView(WorkViewBase, TemplateView):
    template_name = "indigo_api/_work_form_consolidations_form.html"

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = formset = ConsolidationsBaseFormset(self.request.POST,
                                                    user=self.request.user,
                                                    work=self.work,
                                                    prefix="consolidations",
                                                    form_kwargs={"work":self.work,
                                                                 "user": self.request.user})

        initial = []
        if formset.is_valid():
            for form in formset.forms:
                delete = form.cleaned_data.get("DELETE")
                if delete and not form.cleaned_data.get("id"):
                    continue
                initial.append({
                    "date": form.cleaned_data["date"],
                    "id": form.cleaned_data["id"],
                    "DELETE": form.cleaned_data["DELETE"],
                })

            if self.request.POST.get("consolidation") == "add":
                date = self.work.as_at_date()

                initial.append({
                    "date": date
                })

            context["formset"] =  ConsolidationsBaseFormset(
                    user=self.request.user,
                    work=self.work,
                    prefix="consolidations",
                    initial=initial,
                    form_kwargs={"work": self.work,
                                 "user": self.request.user}
                )

        context["work"] = self.work
        return context
