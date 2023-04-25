import logging
from collections import defaultdict, Counter
from datetime import timedelta, date
from itertools import chain, groupby
import json
from lxml import etree

from actstream import action
from actstream.models import Action
from django.contrib.auth.models import User
from django.db.models import Count, Subquery, IntegerField, OuterRef, Prefetch
from django.db.models.functions import Extract
from django.contrib import messages
from django.http import QueryDict
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import ListView, TemplateView, UpdateView
from django.views.generic.list import MultipleObjectMixin

from indigo_api.models import Annotation, Country, Task, Work, Amendment, Subtype, Locality, TaskLabel, Document
from indigo_api.views.documents import DocumentViewSet
from indigo_metrics.models import DailyWorkMetrics, WorkMetrics, DailyPlaceMetrics

from .base import AbstractAuthedIndigoView, PlaceViewBase

from indigo_app.forms import WorkFilterForm, PlaceSettingsForm, ExplorerForm
from indigo_app.xlsx_exporter import XlsxExporter
from indigo_metrics.models import DocumentMetrics

log = logging.getLogger(__name__)


class PlaceMetricsHelper:
    def add_activity_metrics(self, places, metrics, since):
        # fold metrics into countries
        for place in places:
            place.activity_history = json.dumps([
                [m.date.isoformat(), m.n_activities]
                for m in self.add_zero_days(metrics.get(place, []), since)
            ])

    def add_zero_days(self, metrics, since):
        """ Fold zeroes into the daily metrics
        """
        today = date.today()
        d = since
        i = 0
        output = []

        while d <= today:
            if i < len(metrics) and metrics[i].date == d:
                output.append(metrics[i])
                i += 1
            else:
                # add a zero
                output.append(DailyPlaceMetrics(date=d))
            d = d + timedelta(days=1)

        return output


class PlaceListView(AbstractAuthedIndigoView, TemplateView, PlaceMetricsHelper):
    template_name = 'place/list.html'

    def dispatch(self, request, **kwargs):
        if Country.objects.count() == 1:
            return redirect('place', place=Country.objects.all()[0].place_code)

        return super().dispatch(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['countries'] = Country.objects\
            .prefetch_related('country')\
            .annotate(n_works=Subquery(
                Work.objects.filter(country=OuterRef('pk'), locality=None)
                .values('country')
                .annotate(cnt=Count('pk'))
                .values('cnt'),
                output_field=IntegerField()
            ))\
            .annotate(n_open_tasks=Subquery(
                Task.objects.filter(state__in=Task.OPEN_STATES, country=OuterRef('pk'), locality=None)
                .values('country')
                .annotate(cnt=Count('pk'))
                .values('cnt'),
                output_field=IntegerField()
            ))\
            .annotate(p_breadth_complete=Subquery(
                DailyWorkMetrics.objects
                .filter(place_code__iexact=OuterRef('country_id'), locality__exact='')
                .order_by('-date')
                .values('p_breadth_complete')[:1],
                output_field=IntegerField()
            ))\
            .all()

        # place activity
        since = now() - timedelta(days=14)
        metrics = DailyPlaceMetrics.objects\
            .prefetch_related('country')\
            .filter(locality=None, date__gte=since)\
            .order_by('country', 'date')\
            .all()

        # group by country
        metrics = {
            country: list(group)
            for country, group in groupby(metrics, lambda m: m.country)}
        self.add_activity_metrics(context['countries'], metrics, since.date())

        # page counts
        for c in context['countries']:
            c.n_pages = DocumentMetrics.calculate_for_place(c.code)['n_pages'] or 0
            # ensure zeroes
            c.n_works = c.n_works or 0

        return context


class PlaceDetailView(PlaceViewBase, TemplateView):
    template_name = 'place/detail.html'
    tab = 'overview'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        works = Work.objects.filter(country=self.country, locality=self.locality) \
            .order_by('-updated_at')

        context['recently_updated_works'] = self.get_recently_updated_works()
        context['recently_created_works'] = self.get_recently_created_works()
        context['subtypes'] = self.get_works_by_subtype(works)
        context['total_works'] = sum(p[1] for p in context['subtypes'])
        context['total_page_count'] = DocumentMetrics.calculate_for_place(self.place.place_code)['n_pages'] or 0

        # open tasks
        open_tasks_data = self.calculate_open_tasks()
        context['open_tasks'] = open_tasks_data['open_tasks_chart']
        context['open_tasks_by_label'] = open_tasks_data['labels_chart']
        context['total_open_tasks'] = open_tasks_data['total_open_tasks']

        # place activity - 4 weeks
        since = now() - timedelta(days=7 * 4)
        metrics = DailyPlaceMetrics.objects \
            .filter(country=self.country, locality=self.locality, date__gte=since) \
            .order_by('date') \
            .all()

        context['activity_history'] = json.dumps([
            [m.date.isoformat(), m.n_activities]
            for m in metrics
        ])

        # stubs overview
        context['stubs_count'] = works.filter(stub=True).count()
        context['non_stubs_count'] = works.filter(stub=False).count()
        context['stubs_percentage'] = int((context['stubs_count'] / (works.count() or 1)) * 100)
        context['non_stubs_percentage'] = 100 - context['stubs_percentage']

        # primary works overview
        context['primary_works_count'] = works.filter(parent_work__isnull=True).count()
        context['subsidiary_works_count'] = works.filter(parent_work__isnull=False).count()
        context['primary_works_percentage'] = int((context['primary_works_count'] / (works.count() or 1)) * 100)
        context['subsidiary_works_percentage'] = 100 - context['primary_works_percentage']

        # Completeness
        context['latest_stat'] = DailyWorkMetrics.objects\
            .filter(place_code=self.place.place_code)\
            .order_by('-date')\
            .first()

        # breadth completeness history, most recent 30 days
        metrics = list(DailyWorkMetrics.objects
            .filter(place_code=self.place.place_code)
            .order_by('-date')[:30])
        # latest last
        metrics.reverse()
        if metrics:
            context['latest_completeness_stat'] = metrics[-1]
            context['completeness_history'] = [m.p_breadth_complete for m in metrics]

        # Latest stats
        since = now() - timedelta(days=30)
        task_stats = self.get_tasks_stats(since)
        context['new_tasks_added'] = task_stats['new_tasks_added']
        context['tasks_completed'] = task_stats['tasks_completed']
        context['new_works_added'] = works.filter(created_at__gte=since).count()

        # top most active users
        context['top_contributors'] = self.get_top_contributors()

        return context

    def get_recently_updated_works(self):
        # TODO: this should also factor in documents that have been updated
        return Work.objects \
            .filter(country=self.country, locality=self.locality) \
            .order_by('-updated_at')[:5]

    def get_tasks_stats(self, since):
        tasks = Task.objects.filter(country=self.country, locality=self.locality)
        tasks_completed = tasks.filter(state=Task.DONE, closed_at__gte=since).count()
        new_tasks_added = tasks.filter(state=Task.OPEN, created_at__gte=since).count()

        return {"new_tasks_added": new_tasks_added, "tasks_completed": tasks_completed}

    def get_top_contributors(self):
        top_contributors = Task.objects\
            .filter(country=self.country, locality=self.locality, state='done')\
            .values('submitted_by_user')\
            .annotate(task_count=Count('submitted_by_user'))\
            .exclude(task_count=0)\
            .order_by('-task_count')[:10]

        users = {u.id: u for u in User.objects.filter(id__in=[c['submitted_by_user'] for c in top_contributors])}
        for user in top_contributors:
            user['user'] = users[user['submitted_by_user']]

        return top_contributors

    def get_recently_created_works(self):
        return Work.objects \
                   .filter(country=self.country, locality=self.locality) \
                   .order_by('-created_at')[:5]

    def get_works_by_subtype(self, works):
        pairs = list(Counter([Subtype.for_abbreviation(w.subtype) for w in works]).items())
        pairs = [list(p) for p in pairs]
        # sort by count, decreasing
        pairs.sort(key=lambda p: p[1], reverse=True)

        total = sum(x[1] for x in pairs)
        for p in pairs:
            p.append(int((p[1] / (total or 1)) * 100))

        return pairs

    def calculate_open_tasks(self):
        tasks = Task.objects.unclosed().filter(country=self.country, locality=self.locality)
        total_open_tasks = tasks.count()
        pending_review_tasks = tasks.filter(state='pending_review').count()
        open_tasks = tasks.filter(state='open').exclude(assigned_to__isnull=False).count()
        assigned_tasks = tasks.filter(state='open').exclude(assigned_to=None).count()

        open_tasks_chart = [{
                'state': 'open',
                'state_string': 'Open',
                'count': open_tasks,
                'percentage': int((open_tasks / (total_open_tasks or 1)) * 100)
            },
            {
                'state': 'assigned',
                'state_string': 'Assigned',
                'count': assigned_tasks,
                'percentage': int((assigned_tasks / (total_open_tasks or 1)) * 100)
            },
            {
                'state': 'pending_review',
                'state_string': 'Pending review',
                'count': pending_review_tasks,
                'percentage': int((pending_review_tasks / (total_open_tasks or 1)) * 100)
            }]

        # open tasks by label
        labels = TaskLabel.objects.filter(tasks__in=tasks) \
            .annotate(n_tasks=Count('tasks__id'))

        labels_chart = []
        for l in labels:
            labels_chart.append({
                'count': l.n_tasks,
                'title': l.title,
                'slug': l.slug,
                'percentage': int((l.n_tasks / (total_open_tasks or 1)) * 100)
            })

        return {"open_tasks_chart": open_tasks_chart, "labels_chart": labels_chart, "total_open_tasks": total_open_tasks}


class PlaceWorksView(PlaceViewBase, ListView):
    template_name = 'place/works.html'
    tab = 'works'
    context_object_name = 'works'
    paginate_by = 50
    js_view = 'PlaceWorksView WorkFilterFormView'

    def get(self, request, *args, **kwargs):
        params = QueryDict(mutable=True)
        params.update(request.GET)

        # set defaults for: sort order, status, stub and subtype
        if not params.get('sortby'):
            params.setdefault('sortby', '-updated_at')

        if not params.get('status'):
            params.setlist('status', WorkFilterForm.declared_fields['status'].initial)

        if not params.get('stub'):
            params.setdefault('stub', 'excl')

        if not params.get('subtype'):
            params.setdefault('subtype', '-')

        self.form = WorkFilterForm(self.country, params)
        self.form.is_valid()

        if params.get('format') == 'xlsx':
            exporter = XlsxExporter(self.country, self.locality)
            return exporter.generate_xlsx(self.get_queryset(), self.get_xlsx_filename(), False)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Work.objects\
            .select_related('parent_work', 'metrics')\
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

    def count_tasks(self, obj, counts):
        obj.task_stats = {'n_%s_tasks' % s: counts.get(s, 0) for s in Task.STATES}
        obj.task_stats['n_tasks'] = sum(counts.values())
        obj.task_stats['n_active_tasks'] = (
            obj.task_stats['n_open_tasks'] +
            obj.task_stats['n_pending_review_tasks'] +
            obj.task_stats['n_blocked_tasks']
        )
        obj.task_stats['pending_task_ratio'] = 100 * (
            obj.task_stats['n_pending_review_tasks'] /
            (obj.task_stats['n_active_tasks'] or 1)
        )
        obj.task_stats['open_task_ratio'] = 100 * (
            obj.task_stats['n_open_tasks'] /
            (obj.task_stats['n_active_tasks'] or 1)
        )
        obj.task_stats['blocked_task_ratio'] = 100 * (
            obj.task_stats['n_blocked_tasks'] /
            (obj.task_stats['n_active_tasks'] or 1)
        )

    def decorate_works(self, works):
        """ Do some calculations that aid listing of works.
        """
        docs_by_id = {d.id: d for w in works for d in w.filtered_docs}
        works_by_id = {w.id: w for w in works}

        # count annotations
        annotations = Annotation.objects.values('document_id') \
            .filter(closed=False) \
            .filter(document__deleted=False) \
            .annotate(n_annotations=Count('document_id')) \
            .filter(document_id__in=docs_by_id)
        for count in annotations:
            docs_by_id[count['document_id']].n_annotations = count['n_annotations']

        # count tasks
        tasks = Task.objects.filter(work__in=works)

        # tasks counts per state and per work
        work_tasks = tasks.values('work_id', 'state').annotate(n_tasks=Count('work_id'))
        task_states = defaultdict(dict)
        for row in work_tasks:
            task_states[row['work_id']][row['state']] = row['n_tasks']

        # summarise task counts per work
        for work_id, states in task_states.items():
            self.count_tasks(works_by_id[work_id], states)

        # tasks counts per state and per document
        doc_tasks = tasks.filter(document_id__in=list(docs_by_id.keys()))\
            .values('document_id', 'state')\
            .annotate(n_tasks=Count('document_id'))
        task_states = defaultdict(dict)
        for row in doc_tasks:
            task_states[row['document_id']][row['state']] = row['n_tasks']

        # summarise task counts per document
        for doc_id, states in task_states.items():
            self.count_tasks(docs_by_id[doc_id], states)

        # decorate works
        for work in works:
            # most recent update, their the work or its documents
            update = max((c for c in chain(work.filtered_docs, [work]) if c.updated_at), key=lambda x: x.updated_at)
            work.most_recent_updated_at = update.updated_at
            work.most_recent_updated_by = update.updated_by_user

            # count annotations
            work.n_annotations = sum(getattr(d, 'n_annotations', 0) for d in work.filtered_docs)

            # ratios
            try:
                # work metrics may not exist
                metrics = work.metrics
            except WorkMetrics.DoesNotExist:
                metrics = None

            if metrics and metrics.n_expected_expressions > 0:
                n_drafts = sum(1 if d.draft else 0 for d in work.filtered_docs)
                n_published = sum(0 if d.draft else 1 for d in work.filtered_docs)
                work.drafts_ratio = 100 * (n_drafts / metrics.n_expected_expressions)
                work.pub_ratio = 100 * (n_published / metrics.n_expected_expressions)
            else:
                work.drafts_ratio = 0
                work.pub_ratio = 0

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        works = context['works']

        self.decorate_works(list(works))

        # total works
        context['total_works'] = Work.objects.filter(country=self.country, locality=self.locality).count()
        # page count
        context['page_count'] = DocumentMetrics.calculate_for_works(works)['n_pages'] or 0

        return context

    def get_xlsx_filename(self):
        return f"legislation {self.kwargs['place']}.xlsx"


class PlaceActivityView(PlaceViewBase, MultipleObjectMixin, TemplateView):
    model = None
    slug_field = 'place'
    slug_url_kwarg = 'place'
    template_name = 'place/activity.html'
    tab = 'activity'

    object_list = None
    page_size = 30
    js_view = ''
    threshold = timedelta(seconds=3)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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


class PlaceMetricsView(PlaceViewBase, TemplateView, PlaceMetricsHelper):
    template_name = 'place/metrics.html'
    tab = 'insights'
    insights_tab = 'metrics'

    def add_zero_years(self, years):
        # ensure zeros
        if years:
            min_year, max_year = min(years.keys()), max(years.keys())
            for year in range(min_year, max_year + 1):
                years.setdefault(year, 0)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['day_options'] = [
            (30, "30 days"),
            (90, "3 months"),
            (180, "6 months"),
            (360, "12 months"),
        ]
        try:
            days = int(self.request.GET.get('days', 180))
        except ValueError:
            days = 180
        context['days'] = days
        since = now() - timedelta(days=days)

        metrics = list(DailyWorkMetrics.objects
            .filter(place_code=self.place.place_code)
            .filter(date__gte=since)
            .order_by('date')
            .all())

        if metrics:
            context['latest_stat'] = metrics[-1]

        # breadth completeness history
        context['completeness_history'] = json.dumps([
            [m.date.isoformat(), m.p_breadth_complete]
            for m in metrics])

        # works and expressions
        context['n_works_history'] = json.dumps([
            [m.date.isoformat(), m.n_works]
            for m in metrics])

        context['n_expressions_history'] = json.dumps([
            [m.date.isoformat(), m.n_expressions]
            for m in metrics])

        # works by year
        works = Work.objects\
            .filter(country=self.country, locality=self.locality)\
            .select_related(None).prefetch_related(None).all()
        years = Counter([int(w.year) for w in works])
        self.add_zero_years(years)
        years = list(years.items())
        years.sort()
        context['works_by_year'] = json.dumps(years)

        # amendments by year
        years = Amendment.objects\
            .filter(amended_work__country=self.country, amended_work__locality=self.locality)\
            .annotate(year=Extract('date', 'year'))\
            .values('year')\
            .annotate(n=Count('id'))\
            .order_by()\
            .all()
        years = {x['year']: x['n'] for x in years}
        self.add_zero_years(years)
        years = list(years.items())
        years.sort()
        context['amendments_by_year'] = json.dumps(years)

        # works by subtype
        def subtype_name(abbr):
            if not abbr:
                return 'Act'
            st = Subtype.for_abbreviation(abbr)
            return st.name if st else abbr
        pairs = list(Counter([subtype_name(w.subtype) for w in works]).items())
        pairs.sort(key=lambda p: p[1], reverse=True)
        context['subtypes'] = json.dumps(pairs)

        # place activity
        metrics = DailyPlaceMetrics.objects \
            .filter(country=self.country, locality=self.locality, date__gte=since) \
            .order_by('date') \
            .all()

        context['activity_history'] = json.dumps([
            [m.date.isoformat(), m.n_activities]
            for m in metrics
        ])

        return context


class PlaceExplorerView(PlaceViewBase, ListView):
    template_name = 'place/explorer.html'
    tab = 'insights'
    insights_tab = 'explorer'
    paginate_by = 50
    context_object_name = 'matches'

    def get(self, request, *args, **kwargs):
        self.form = ExplorerForm(request.GET)
        return super().get(request, *args, **kwargs)

    def has_permission(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['form'] = self.form
        context['n_documents'] = self.n_documents
        self.prettify(context['matches'])

        context['samples'] = [
            ('List introductions containing remarks', '//a:subsection//a:blockList/a:listIntroduction/a:remark', '2'),
            ('Adjacent block lists', '//a:blockList/following-sibling::*[1][self::a:blockList]', '1'),
        ]

        return context

    def get_queryset(self):
        self.n_documents = 0

        if not self.form.is_valid():
            return []

        if self.form.cleaned_data['global_search']:
            documents = Document.objects \
                .undeleted() \
                .order_by('title', '-expression_date')

        else:
            documents = Document.objects \
                .undeleted() \
                .filter(work__country=self.country) \
                .order_by('title', '-expression_date')

            if self.locality:
                documents = documents.filter(work__locality=self.locality)
            elif not self.form.cleaned_data['localities']:
                # explicitly exclude localities
                documents = documents.filter(work__locality=None)

        return self.find(documents, self.form.cleaned_data['xpath'])

    def find(self, documents, xpath):
        """ Return elements that match an xpath expression in a collection of documents.
        """
        matches = []

        for doc in documents:
            namespaces = {
                'a': doc.doc.namespace,
                're': 'http://exslt.org/regular-expressions',
            }
            try:
                elems = list(doc.doc.main.xpath(xpath, namespaces=namespaces))
            except Exception as e:
                self.form.add_error('xpath', str(e))
                return []

            if elems:
                self.n_documents += 1
                try:
                    matches.extend([{
                        'doc': doc,
                        'element': self.normalise(e),
                    } for e in elems])
                except ValueError as e:
                    self.form.add_error('xpath', str(e))

        return matches

    def normalise(self, e):
        # text nodes and attribute values
        if isinstance(e, etree._ElementUnicodeResult):
            return e.getparent()

        if not isinstance(e, etree.ElementBase):
            raise ValueError(f'Expression must produce elements, but found {e.__class__.__name__} instead.')

        return e

    def prettify(self, matches):
        parent = self.form.cleaned_data['parent']

        def parent_context(e):
            if parent == '1':
                return e.getparent()
            if parent == '2':
                return e.getparent().getparent()
            return e

        for match in matches:
            elem = match['element']
            context = parent_context(elem)
            match['xml'] = etree.tostring(context, encoding='utf-8', pretty_print=True).decode('utf-8')

            if self.form.cleaned_data['parent']:
                # we're adding context, so decorate with an attribute we use in the HTML to highlight the real matched element
                elem.attrib['match'] = '1'
                elem = parent_context(elem)

            match['html'] = match['doc'].element_to_html(elem)


class PlaceSettingsView(PlaceViewBase, UpdateView):
    template_name = 'place/settings.html'
    form_class = PlaceSettingsForm
    tab = 'place_settings'

    # permissions
    # TODO: this should be scoped to the country/locality
    permission_required = ('indigo_api.change_placesettings',)

    def get_object(self, *args, **kwargs):
        return self.place.settings

    def form_valid(self, form):
        placesettings = self.object
        placesettings.updated_by_user = self.request.user

        # action signals
        if form.changed_data:
            action.send(self.request.user, verb='updated', action_object=placesettings,
                        place_code=placesettings.place.place_code)

        messages.success(self.request, "Settings updated.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('place_settings', kwargs={'place': self.kwargs['place']})


class PlaceWorksIndexView(PlaceViewBase, TemplateView):
    tab = 'place_settings'
    permission_required = ('indigo_api.change_placesettings',)

    def get(self, request, *args, **kwargs):
        works = Work.objects.filter(country=self.country, locality=self.locality).order_by('publication_date')
        filename = f"Full index for {self.place}.xlsx"

        exporter = XlsxExporter(self.country, self.locality)
        return exporter.generate_xlsx(works, filename, True)


class PlaceLocalitiesView(PlaceViewBase, TemplateView, PlaceMetricsHelper):
    template_name = 'place/localities.html'
    tab = 'localities'
    js_view = 'PlaceListView'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['localities'] = Locality.objects \
            .filter(country=self.country) \
            .annotate(n_works=Count('works')) \
            .annotate(n_open_tasks=Subquery(
                Task.objects.filter(state__in=Task.OPEN_STATES, locality=OuterRef('pk'))
                    .values('locality')
                    .annotate(cnt=Count('pk'))
                    .values('cnt'),
                output_field=IntegerField()
            ))\
            .annotate(p_breadth_complete=Subquery(
                DailyWorkMetrics.objects.filter(locality=OuterRef('code'))
                .order_by('-date')
                .values('p_breadth_complete')[:1],
                output_field=IntegerField()
            ))\
            .all()

        # place activity
        since = now() - timedelta(days=14)
        metrics = DailyPlaceMetrics.objects \
            .filter(country=self.country, date__gte=since) \
            .exclude(locality=None) \
            .order_by('locality', 'date') \
            .all()

        # group by locality
        metrics = {
            country: list(group)
            for country, group in groupby(metrics, lambda m: m.locality)}
        self.add_activity_metrics(context['localities'], metrics, since.date())

        # page counts
        for p in context['localities']:
            p.n_pages = DocumentMetrics.calculate_for_place(p.place_code)['n_pages'] or 0

        return context
