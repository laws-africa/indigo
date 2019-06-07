# coding=utf-8
import logging
import json
from collections import defaultdict
from datetime import timedelta
from itertools import chain

from actstream.models import Action
from django.db.models import Count, Subquery, IntegerField, OuterRef, Prefetch
from django.http import QueryDict
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.generic.list import MultipleObjectMixin

from indigo_api.models import Country, Annotation, Task, Amendment, Work
from indigo_api.serializers import WorkSerializer, DocumentSerializer
from indigo_api.views.works import WorkViewSet
from indigo_api.views.documents import DocumentViewSet
from indigo_metrics.models import DailyWorkMetrics

from .base import AbstractAuthedIndigoView, PlaceViewBase

from indigo_app.forms import WorkFilterForm


log = logging.getLogger(__name__)


class PlaceListView(AbstractAuthedIndigoView, TemplateView):
    template_name = 'place/list.html'
    js_view = ''

    def dispatch(self, request, **kwargs):
        if Country.objects.count == 1:
            return redirect('place', place=Country.objects.all()[0].place_code)

        return super(PlaceListView, self).dispatch(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PlaceListView, self).get_context_data(**kwargs)

        context['countries'] = Country.objects\
            .prefetch_related('country')\
            .annotate(n_works=Count('works'))\
            .annotate(n_open_tasks=Subquery(
                Task.objects.filter(state__in=Task.OPEN_STATES, country=OuterRef('pk'))
                .values('country')
                .annotate(cnt=Count('pk'))
                .values('cnt'),
                output_field=IntegerField()
            ))\
            .all()

        return context


# TODO: WorkFilterForm
class PlaceDetailView(PlaceViewBase, AbstractAuthedIndigoView, TemplateView):
    template_name = 'place/detail.html'
    js_view = 'LibraryView'
    tab = 'works'

    def get(self, request, *args, **kwargs):
        params = QueryDict(mutable=True)
        params.update(request.GET)

        # set defaults for: sort order, status, stub and subtype
        if not params.get('sortby'):
            params.setdefault('sortby', '-updated_at')

        if not params.get('status'):
            params.setlist('status', ['published', 'draft'])

        if not params.get('stub'):
            params.setdefault('stub', 'excl')

        if not params.get('subtype'):
            params.setdefault('subtype', '-')

        self.form = WorkFilterForm(self.country, params)
        self.form.is_valid()

        return super(PlaceDetailView, self).get(request, *args, **kwargs)    

    def get_queryset(self):
        queryset = Work.objects\
            .select_related('parent_work')\
            .filter(country=self.country, locality=self.locality)\
            .distinct()\
            .order_by('-updated_at')

        queryset = self.form.filter_queryset(queryset)

        # prefetch and filter documents
        queryset = queryset.prefetch_related(Prefetch(
            'document_set',
            to_attr='filtered_docs',
            queryset=self.form.filter_document_queryset(DocumentViewSet.queryset)
        ))

        return queryset

    def decorate_works(self, works):
        """ Do some calculations that aid listing of works.
        """
        docs_by_id = {d.id: d for w in works for d in w.filtered_docs}

        # count annotations
        annotations = Annotation.objects.values('document_id') \
            .filter(closed=False) \
            .filter(document__deleted=False) \
            .annotate(n_annotations=Count('document_id')) \
            .filter(document_id__in=docs_by_id.keys())
        for count in annotations:
            docs_by_id[count['document_id']].n_annotations = count['n_annotations']

        for work in works:
            # most recent update, their the work or its documents
            update = max((c for c in chain(work.filtered_docs, [work]) if c.updated_at), key=lambda x: x.updated_at)
            work.most_recent_updated_at = update.updated_at
            work.most_recent_updated_by = update.updated_by_user

            # count annotations
            work.n_annotations = sum(getattr(d, 'n_annotations', 0) for d in work.filtered_docs)

    def get_context_data(self, **kwargs):
        context = super(PlaceDetailView, self).get_context_data(**kwargs)
        context['form'] = self.form

        serializer = WorkSerializer(context={'request': self.request}, many=True)
        context['works'] = works = self.get_queryset().all()

        self.decorate_works(works)

        context['works_json'] = json.dumps(serializer.to_representation(works))

        serializer = DocumentSerializer(context={'request': self.request}, many=True)
        docs = DocumentViewSet.queryset.filter(work__country=self.country, work__locality=self.locality)

        context['documents_json'] = json.dumps(serializer.to_representation(docs))

        # tasks for place
        tasks = Task.objects.filter(work__country=self.country, work__locality=self.locality)

        # tasks counts per state and per work
        work_tasks = tasks.values('work_id', 'state').annotate(n_tasks=Count('work_id'))
        task_states = defaultdict(dict)
        for row in work_tasks:
            task_states[row['work_id']][row['state']] = row['n_tasks']

        # summarise task counts per work
        work_tasks = {}
        for work_id, states in task_states.iteritems():
            work_tasks[work_id] = {'n_%s_tasks' % s: states.get(s, 0) for s in Task.STATES}
            work_tasks[work_id]['n_tasks'] = sum(states.itervalues())
        context['work_tasks_json'] = json.dumps(work_tasks)

        # tasks counts per state and per document
        doc_tasks = tasks.values('document_id', 'state').annotate(n_tasks=Count('document_id'))
        task_states = defaultdict(dict)
        for row in doc_tasks:
            task_states[row['document_id']][row['state']] = row['n_tasks']

        # summarise task counts per document
        document_tasks = {}
        for doc_id, states in task_states.iteritems():
            document_tasks[doc_id] = {'n_%s_tasks' % s: states.get(s, 0) for s in Task.STATES}
            document_tasks[doc_id]['n_tasks'] = sum(states.itervalues())
        context['document_tasks_json'] = json.dumps(document_tasks)

        # summarise amendments per work
        amendments = Amendment.objects.values('amended_work_id')\
            .filter(amended_work_id__in=[w.id for w in works])\
            .annotate(n_amendments=Count('pk'))\
            .order_by()\
            .all()

        amendments = {a['amended_work_id']: {'n_amendments': a['n_amendments']} for a in amendments}
        context['work_n_amendments_json'] = json.dumps(amendments)

        # breadth completeness history
        context['completeness_history'] = list(DailyWorkMetrics.objects
            .filter(place_code=self.place.place_code)
            .order_by('-date')
            .values_list('p_breadth_complete', flat=True)[:30])
        context['completeness_history'].reverse()
        context['p_breadth_complete'] = context['completeness_history'][-1] if context['completeness_history'] else None

        return context


class PlaceActivityView(PlaceViewBase, MultipleObjectMixin, TemplateView):
    model = None
    slug_field = 'place'
    slug_url_kwarg = 'place'
    template_name = 'place/activity.html'
    tab = 'activity'

    object_list = None
    page_size = 20
    js_view = ''
    threshold = timedelta(seconds=3)

    def get_context_data(self, **kwargs):
        context = super(PlaceActivityView, self).get_context_data(**kwargs)

        activity = Action.objects.filter(data__place_code=self.place.place_code)
        activity = self.coalesce_entries(activity)

        paginator, page, versions, is_paginated = self.paginate_queryset(activity, self.page_size)
        context.update({
            'paginator': paginator,
            'page_obj': page,
            'is_paginated': is_paginated,
            'place': self.place,
        })

        return context

    def coalesce_entries(self, stream):
        """ If more than 1 task were added to a workflow at once, rather display something like
        '<User> added <n> tasks to <workflow> at <time>'
        """
        activity_stream = []
        added_stash = []
        for i, action in enumerate(stream):
            if i == 0:
                # is the first action an addition?
                if getattr(action, 'verb', None) == 'added':
                    added_stash.append(action)
                else:
                    activity_stream.append(action)

            else:
                # is a subsequent action an addition?
                if getattr(action, 'verb', None) == 'added':
                    # if yes, was the previous action also an addition?
                    prev = stream[i - 1]
                    if getattr(prev, 'verb', None) == 'added':
                        # if yes, did the two actions happen close together and was it on the same workflow?
                        if prev.timestamp - action.timestamp < self.threshold \
                                and action.target_object_id == prev.target_object_id:
                            # if yes, the previous action was added to the stash and
                            # this action should also be added to the stash
                            added_stash.append(action)
                        else:
                            # if not, this action should start a new stash,
                            # but first squash, add and delete the existing stash
                            stash = self.combine(added_stash)
                            activity_stream.append(stash)
                            added_stash = []
                            added_stash.append(action)
                    else:
                        # the previous action wasn't an addition
                        # so this action should start a new stash
                        added_stash.append(action)
                else:
                    # this action isn't an addition, so squash and add the existing stash first
                    # (if it exists) and then add this action
                    if len(added_stash) > 0:
                        stash = self.combine(added_stash)
                        activity_stream.append(stash)
                        added_stash = []
                    activity_stream.append(action)

        return activity_stream

    def combine(self, stash):
        first = stash[0]
        if len(stash) == 1:
            return first
        else:
            workflow = first.target
            action = Action(actor=first.actor, verb='added %d tasks to' % len(stash), action_object=workflow)
            action.timestamp = first.timestamp
            return action
