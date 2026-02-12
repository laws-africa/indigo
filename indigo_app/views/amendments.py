import logging

from django.views.generic import DetailView, UpdateView, CreateView, DeleteView, View
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
import datetime

from indigo.view_mixins import AtomicPostMixin
from django_fsm import has_transition_perm
from indigo_api.models import Amendment, AmendmentInstruction, ArbitraryExpressionDate
from indigo_app.forms.amendments import AmendmentInstructionForm

from .works import WorkViewBase, WorkDependentView

log = logging.getLogger(__name__)


class WorkAmendmentsView(WorkViewBase, DetailView):
    template_name_suffix = '/amendments'
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


class AmendmentDetailViewBase(WorkDependentView):
    amendment_url_kwarg = 'amendment_id'
    amendment = None

    def get_amendment(self):
        if not self.amendment:
            self.amendment = get_object_or_404(self.work.amendments, pk=self.kwargs[self.amendment_url_kwarg])
        return self.amendment

    def get_context_data(self, **kwargs):
        kwargs.setdefault('amendment', self.get_amendment())
        return super().get_context_data(**kwargs)


class WorkAmendmentDropdownView(AmendmentDetailViewBase, DetailView):
    model = Amendment
    pk_url_kwarg = 'amendment_id'
    template_name = 'indigo_api/timeline/_amendment_dropdown.html'
    context_object_name = 'amendment'

    def get_object(self, queryset=None):
        return self.get_amendment()


class AmendmentInstructionsView(AmendmentDetailViewBase, DetailView):
    """View and list instructions for an amendment. Supports both HTMX (for embedding instructions) and full page view."""
    model = Amendment
    pk_url_kwarg = 'amendment_id'
    template_name = 'indigo_api/amendment/instructions.html'
    context_object_name = 'amendment'
    tab = 'amendments'

    def get_object(self, queryset=None):
        return self.get_amendment()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edit_button"] = bool(self.request.htmx)
        return context

    def get_template_names(self):
        if self.request.htmx:
            return ['indigo_api/amendment/_instruction_list.html']
        return [self.template_name]


class AmendmentInstructionDetailViewBase(AmendmentDetailViewBase):
    """ Base view for amendment instruction detail views. """
    model = AmendmentInstruction
    pk_url_kwarg = 'pk'
    context_object_name = 'instruction'

    def get_queryset(self):
        return self.get_amendment().instructions.all()


class AmendmentInstructionDetailView(AmendmentInstructionDetailViewBase, DetailView):
    """ HTMX view for displaying an amendment instruction."""
    template_name = 'indigo_api/amendment/_instruction_detail.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            can_apply=self.request.GET.get("apply") is not None,
            can_edit=self.request.GET.get("edit") is not None,
            **kwargs)


class AmendmentInstructionCreateView(AtomicPostMixin, AmendmentDetailViewBase, CreateView):
    model = AmendmentInstruction
    form_class = AmendmentInstructionForm
    template_name = 'indigo_api/amendment/_instruction_form.html'
    context_object_name = 'instruction'
    permission_required = ('indigo_api.add_amendmentinstruction',)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('form_action', reverse('work_amendment_instruction_new', kwargs={
            'frbr_uri': self.kwargs['frbr_uri'],
            'amendment_id': self.kwargs['amendment_id'],
        }))
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.instance.amendment = self.get_amendment()
        form.instance.created_by_user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('work_amendment_instruction_detail', kwargs={
            'frbr_uri': self.kwargs['frbr_uri'],
            'amendment_id': self.kwargs['amendment_id'],
            'pk': self.object.pk,
        }) + "?edit"


class AmendmentInstructionEditView(AtomicPostMixin, AmendmentInstructionDetailViewBase, UpdateView):
    """ HTMX view for editing an amendment instruction."""
    form_class = AmendmentInstructionForm
    template_name = 'indigo_api/amendment/_instruction_form.html'
    permission_required = ('indigo_api.change_amendmentinstruction',)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('form_action', reverse('work_amendment_instruction_edit', kwargs={
            'frbr_uri': self.kwargs['frbr_uri'],
            'amendment_id': self.kwargs['amendment_id'],
            'pk': self.kwargs['pk'],
        }))
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('work_amendment_instruction_detail', kwargs={
            'frbr_uri': self.kwargs['frbr_uri'],
            'amendment_id': self.kwargs['amendment_id'],
            'pk': self.object.pk,
        }) + "?edit"


class AmendmentInstructionDeleteView(AtomicPostMixin, AmendmentInstructionDetailViewBase, DeleteView):
    http_method_names = ['post']
    permission_required = ('indigo_api.delete_amendmentinstruction',)

    def get_success_url(self):
        return reverse('work_amendment_instructions', kwargs={
            'frbr_uri': self.kwargs['frbr_uri'],
            'amendment_id': self.kwargs['amendment_id'],
        })


class AmendmentInstructionClearView(AtomicPostMixin, AmendmentDetailViewBase, View):
    http_method_names = ['post']
    permission_required = ('indigo_api.delete_amendmentinstruction',)

    def post(self, request, *args, **kwargs):
        amendment = self.get_amendment()
        amendment.instructions.all().delete()
        return redirect(reverse('work_amendment_instructions', kwargs={
            'frbr_uri': self.kwargs['frbr_uri'],
            'amendment_id': self.kwargs['amendment_id'],
        }))


class AmendmentInstructionStateChangeView(AtomicPostMixin, AmendmentInstructionDetailViewBase, View):
    http_method_names = ['post']
    permission_required = ('indigo_api.change_amendmentinstruction',)
    change = None

    def post(self, request, *args, **kwargs):
        instruction = self.get_object()
        user = request.user

        if self.change == 'applied':
            if not has_transition_perm(instruction.apply, user):
                raise PermissionDenied
            instruction.apply(user)
        elif self.change == 'unapplied':
            if not has_transition_perm(instruction.unapply, user):
                raise PermissionDenied
            instruction.unapply()
        else:
            raise PermissionDenied

        # the ?apply indicates that the template can show the apply/unapply button
        url = reverse('work_amendment_instruction_detail', kwargs={
            "frbr_uri": self.kwargs['frbr_uri'],
            "amendment_id": self.kwargs['amendment_id'],
            "pk": instruction.pk
        }) + "?apply"
        return redirect(url)
