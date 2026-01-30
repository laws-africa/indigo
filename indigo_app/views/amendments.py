import logging

from django.views.generic import DetailView, UpdateView, CreateView
from django.urls import reverse
from django.shortcuts import redirect
import datetime

from indigo.view_mixins import AtomicPostMixin
from indigo_api.models import Amendment, ArbitraryExpressionDate

from .works import WorkViewBase, WorkDependentView

log = logging.getLogger(__name__)


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


class WorkAmendmentUpdateView(AtomicPostMixin, WorkDependentView, UpdateView):
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

    def get_object(self, queryset=None):
        return self.work.amendments


class AddWorkAmendmentView(AtomicPostMixin, WorkDependentView, CreateView):
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
