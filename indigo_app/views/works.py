# coding=utf-8
import json
import logging
from collections import Counter
from itertools import chain
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.views.generic import DetailView, FormView, UpdateView, CreateView, DeleteView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from reversion import revisions as reversion
import datetime

from indigo.plugins import plugins
from indigo_api.models import Subtype, Work, Amendment, Document, Task, PublicationDocument, \
    ArbitraryExpressionDate, Commencement, Workflow
from indigo_api.serializers import WorkSerializer
from indigo_api.views.attachments import view_attachment
from indigo_api.signals import work_changed
from indigo_app.revisions import decorate_versions
from indigo_app.forms import BatchCreateWorkForm, ImportDocumentForm, WorkForm, CommencementForm, NewCommencementForm
from indigo_metrics.models import WorkMetrics

from .base import AbstractAuthedIndigoView, PlaceViewBase


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
        # get initial, amendment, consolidation dates
        dates = work.possible_expression_dates()
        # add assent, publication, repeal, commencement dates
        other_dates = [
            ('assent_date', work.assent_date),
            ('publication_date', work.publication_date),
            ('repealed_date', work.repealed_date)
        ]
        for c in work.commencements.all():
            other_dates.append(('commencement_date', c.date))

        for name, date in other_dates:
            if date:
                if date not in [entry['date'] for entry in dates]:
                    dates.append({
                        'date': date,
                        name: True,
                    })
                else:
                    # add to existing events (e.g. if publication and commencement dates are the same)
                    for entry in dates:
                        if entry['date'] == date:
                            entry[name] = True

        dates.sort(key=lambda x: x['date'], reverse=True)

        # add expressions and commencement and amendment objects
        for event in dates:
            date = event['date']
            if event.get('commencement_date'):
                event['commencements'] = work.commencements.filter(date=date).all()
            if event.get('amendment'):
                event['amendments'] = work.amendments.filter(date=date).all()
            if event.get('consolidation'):
                event['consolidations'] = work.arbitrary_expression_dates.filter(date=date).all()
            event['expressions'] = work.expressions().filter(expression_date=date).all()

        return dates

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
        kwargs['place'] = self.place
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(EditWorkView, self).get_context_data(**kwargs)
        context['doctypes'] = self.doctypes()
        context['subtypes'] = Subtype.objects.order_by('name').all()
        return context

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
                for doc in Document.objects.filter(work=self.work, expression_date=old_date):
                    doc.expression_date = self.work.publication_date
                    doc.save()

        # if the work title changes, ensure matching document titles do too
        if 'title' in form.changed_data:
            old_title = form.initial['title']
            if old_title:
                for doc in Document.objects.filter(work=self.work, title=old_title):
                    doc.title = self.work.title
                    doc.save()

        if form.has_changed():
            # signals
            work_changed.send(sender=self.__class__, work=self.work, request=self.request)
            messages.success(self.request, "Work updated.")

            # rename publication-document if frbr_uri has changed
            if 'frbr_uri' in form.changed_data:
                try:
                    self.work.publication_document.save()
                except PublicationDocument.DoesNotExist:
                    pass

        return resp

    def get_success_url(self):
        return reverse('work', kwargs={'frbr_uri': self.work.frbr_uri})


class AddWorkView(PlaceViewBase, CreateView):
    model = Work
    js_view = 'WorkDetailView'
    form_class = WorkForm
    prefix = 'work'
    permission_required = ('indigo_api.add_work',)
    is_create = True
    PUB_DATE_OPTIONAL_COUNTRIES = []

    def get_form_kwargs(self):
        kwargs = super(AddWorkView, self).get_form_kwargs()

        work = Work()
        work.country = self.country
        work.locality = self.locality
        kwargs['instance'] = work
        kwargs['place'] = self.place

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
        context['publication_date_optional'] = self.country.code in self.PUB_DATE_OPTIONAL_COUNTRIES

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

    def get_context_data(self, **kwargs):
        context = super(WorkCommencementsView, self).get_context_data(**kwargs)
        context['provisions'] = provisions = self.work.all_commenceable_provisions()
        context['uncommenced_provisions'] = self.work.all_uncommenced_provisions()
        context['commencements'] = commencements = self.work.commencements.all().reverse()
        context['has_all_provisions'] = any(c.all_provisions for c in commencements)
        context['has_main_commencement'] = any(c.main for c in commencements)
        context['everything_commenced'] = context['has_all_provisions'] or (context['provisions'] and not context['uncommenced_provisions'])

        provision_set = {p.id: p for p in provisions}
        for commencement in commencements:
            # rich description of provisions
            commencement.provision_items = [provision_set.get(p, p) for p in commencement.provisions]
            # possible options
            commencement.possible_provisions = self.get_possible_provisions(commencement, commencements, provisions)

        return context

    def get_possible_provisions(self, commencement, commencements, provisions):
        # provisions commenced by everything else
        commenced = set(p for comm in commencements if comm != commencement for p in comm.provisions)
        return [p for p in provisions if p.id not in commenced]


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
        kwargs['provisions'] = self.work.all_commenceable_provisions()
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
        context['consolidation_date'] = self.work.as_at_date or self.place.settings.as_at_date or datetime.date.today()
        return context


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

        # commencement
        commencement = [{
            'rel': 'commenced by',
            'work': c.commencing_work,
            'date': c.date,
        } for c in self.work.commencements.all() if c.commencing_work]
        commencement = commencement + [{
            'rel': 'commenced',
            'work': c.commenced_work,
            'date': c.date,
        } for c in self.work.commencements_made.all()]
        context['commencement'] = commencement

        context['no_related'] = (not family and not amended and not amended_by and not repeals and not commencement)

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

        Task.decorate_potential_assignees(context['tasks'], self.country)
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
    template_name = 'indigo_api/work_new_batch.html'
    # permissions
    permission_required = ('indigo_api.bulk_add_work',)
    form_class = BatchCreateWorkForm

    _bulk_creator = None

    @property
    def bulk_creator(self):
        if not self._bulk_creator:
            locality_code = self.locality.code if self.locality else None
            self._bulk_creator = plugins.for_locale('bulk-creator', self.country.code, None, locality_code)
            self._bulk_creator.country = self.country
            self._bulk_creator.locality = self.locality
            self._bulk_creator.request = self.request
            self._bulk_creator.user = self.request.user
            self._bulk_creator.testing = False
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
        context = super(BatchAddWorkView, self).get_context_data(**kwargs)
        context['bulk_creator'] = self.bulk_creator
        return context

    def form_valid(self, form):
        error = None
        works = None
        dry_run = 'preview' in form.data

        if ('import' in form.data or 'preview' in form.data) and (
            # either no gsheets, or we have a sheet name
            not self.bulk_creator.is_gsheets_enabled or form.cleaned_data.get('sheet_name')):

            workflow = form.cleaned_data['workflow']

            try:
                table = self.bulk_creator.get_datatable(
                    form.cleaned_data['spreadsheet_url'],
                    form.cleaned_data['sheet_name'])

                works = self.bulk_creator.create_works(table, dry_run, workflow)
                if not dry_run:
                    messages.success(self.request, f"Imported {len([w for w in works if w.status == 'success'])} works.")
            except ValidationError as e:
                error = str(e)

        context_data = self.get_context_data(works=works, error=error, form=form, dry_run=dry_run)
        return self.render_to_response(context_data)


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
            importer.create_from_upload(upload, document, self.request)
        except ValueError as e:
            log.error("Error during import: %s" % str(e), exc_info=e)
            return JsonResponse({'file': str(e) or "error during import"}, status=400)

        document.updated_by_user = self.request.user
        document.save_with_revision(self.request.user)

        return JsonResponse({'location': reverse('document', kwargs={'doc_id': document.id})})


class WorkPopupView(WorkViewBase, DetailView):
    template_name = 'indigo_api/work_popup.html'

