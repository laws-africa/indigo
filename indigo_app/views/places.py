import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import timedelta, date
from itertools import chain, groupby
import json
from typing import List

from lxml import etree

from actstream import action
from actstream.models import Action
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Count, Subquery, IntegerField, OuterRef, Prefetch, Case, When, Value, Q
from django.db.models.functions import Extract
from django.contrib import messages
from django.http import QueryDict
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django.views.generic import ListView, TemplateView, UpdateView, FormView, DetailView
from django.views.generic.list import MultipleObjectMixin
from django_htmx.http import push_url
from django.db.models import Q

from indigo_api.models import Annotation, Country, Task, Work, Amendment, Subtype, Locality, TaskLabel, Document, TaxonomyTopic
from indigo_api.timeline import describe_publication_event
from indigo_api.views.documents import DocumentViewSet
from indigo_metrics.models import DailyWorkMetrics, WorkMetrics, DailyPlaceMetrics

from .base import AbstractAuthedIndigoView, PlaceViewBase

from indigo_app.forms import WorkFilterForm, PlaceSettingsForm, PlaceUsersForm, ExplorerForm, WorkBulkActionsForm
from indigo_app.xlsx_exporter import XlsxExporter
from indigo_metrics.models import DocumentMetrics
from indigo_social.badges import badges

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


class PlaceUsersView(PlaceViewBase, FormView):
    template_name = 'place/users.html'
    tab = 'place_users'
    form_class = PlaceUsersForm

    def get_initial(self):
        initial = super().get_initial()
        initial["users"] = [u.id for u in User.objects.filter(badges_earned__slug=f"country-{self.country.code.lower()}")]
        return initial

    def form_valid(self, form):
        users = User.objects.all()
        country_badge = badges.registry.get(f"country-{self.country.code.lower()}")
        for user in users:
            if str(user.id) in form.cleaned_data['users']:
                country_badge.possibly_award(user=user)
            else:
                country_badge.unaward(user=user)
        messages.success(self.request, "Users updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('place_users', kwargs={'place': self.kwargs['place']})


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


class PlaceWorksView(PlaceViewBase, ListView):
    template_name = 'indigo_app/place/works.html'
    tab = 'works'
    context_object_name = 'works'
    paginate_by = 50
    http_method_names = ['post', 'get']

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.form = WorkFilterForm(self.country, request.POST or request.GET)
        self.form.is_valid()

        if self.form.data.get('format') == 'xlsx':
            exporter = XlsxExporter(self.country, self.locality)
            return exporter.generate_xlsx(self.get_queryset(), f"legislation {self.kwargs['place']}.xlsx", False)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Work.objects \
            .select_related('parent_work', 'metrics') \
            .filter(country=self.country, locality=self.locality) \
            .distinct() \
            .order_by('-created_at')

        queryset = self.form.filter_queryset(queryset)

        # prefetch and filter documents
        # TODO
        queryset = queryset.prefetch_related(Prefetch(
            'document_set',
            to_attr='filtered_docs',
            queryset=self.form.filter_document_queryset(DocumentViewSet.queryset)
        ))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        works = context["works"]
        context['total_works'] = Work.objects.filter(country=self.country, locality=self.locality).count()
        context['page_count'] = DocumentMetrics.calculate_for_works(works)['n_pages'] or 0
        context['facets_url'] = (
            reverse('place_works_facets', kwargs={'place': self.kwargs['place']}) +
            '?' + (self.request.POST or self.request.GET).urlencode()
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        resp = super().render_to_response(context, **response_kwargs)
        if self.request.htmx:
            # encode request.POST as a URL string
            url = f"{self.request.path}?{self.request.POST.urlencode()}"
            resp = push_url(resp, url)
        return resp

    def get_template_names(self):
        if self.request.htmx:
            return ['indigo_app/place/_works_list.html']
        return super().get_template_names()


@dataclass
class FacetItem:
    label: str
    value: str
    count: int
    selected: bool


@dataclass
class Facet:
    label: str
    name: str
    type: str
    items: List[FacetItem] = field(default_factory=list)


@dataclass
class OverviewDataEntry:
    key: str
    value: str
    overridden: bool = False


class PlaceWorksFacetsView(PlaceViewBase, TemplateView):
    template_name = 'indigo_app/place/_works_facets.html'

    def get(self, request, *args, **kwargs):
        self.form = WorkFilterForm(self.country, request.GET)
        self.form.is_valid()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['form'] = self.form
        context['taxonomy_toc'] = TaxonomyTopic.get_toc_tree(self.request.GET, all_topics=False)

        qs = Work.objects.filter(country=self.country, locality=self.locality)

        # build facets
        context["work_facets"] = work_facets = []
        self.facet_subtype(work_facets, qs)
        self.facet_principal(work_facets, qs)
        self.facet_stub(work_facets, qs)
        self.facet_tasks(work_facets, qs)
        self.facet_publication_document(work_facets, qs)
        self.facet_primary(work_facets, qs)
        self.facet_commencement(work_facets, qs)
        self.facet_amendment(work_facets, qs)
        self.facet_consolidation(work_facets, qs)
        self.facet_repeal(work_facets, qs)
        self.facet_taxonomy(context['taxonomy_toc'], qs)

        context["document_facets"] = doc_facets = []
        self.facet_points_in_time(doc_facets, qs)
        self.facet_point_in_time_status(doc_facets, qs)

        return context

    def facet_subtype(self, facets, qs):
        # count doctypes, subtypes in the current place first, so these are always shown as an option
        counts_in_place = {c["doctype"]: c["count"] for c in qs.filter(subtype=None).values("doctype").annotate(count=Count("doctype")).order_by()}
        counts_subtype_in_place = {c["subtype"]: c["count"] for c in qs.values("subtype").annotate(count=Count("subtype")).order_by()}
        counts_in_place.update(counts_subtype_in_place)

        qs = self.form.filter_queryset(qs, exclude="subtype")
        # count doctypes, subtypes by code
        counts = {c["doctype"]: c["count"] for c in qs.filter(subtype=None).values("doctype").annotate(count=Count("doctype")).order_by()}
        counts_subtype = {c["subtype"]: c["count"] for c in qs.values("subtype").annotate(count=Count("subtype")).order_by()}
        counts.update(counts_subtype)
        items = [
            FacetItem(
                c[1],
                c[0],
                counts.get(c[0], 0),
                c[0] in self.form.cleaned_data.get("subtype", [])
            )
            for c in self.form.fields["subtype"].choices
            if counts_in_place.get(c[0])
        ]
        facets.append(Facet("Type", "subtype", "checkbox", items))

    def facet_principal(self, facets, qs):
        qs = self.form.filter_queryset(qs, exclude="principal")
        counts = qs.aggregate(
            principal_counts=Count("pk", filter=Q(principal=True), distinct=True),
            not_principal_counts=Count("pk", filter=Q(principal=False), distinct=True),
        )
        items = [
            FacetItem(
                "Principal",
                "principal",
                counts.get("principal_counts", 0),
                "principal" in self.form.cleaned_data.get("principal", [])
            ),
            FacetItem(
                "Not principal",
                "not_principal",
                counts.get("not_principal_counts", 0),
                "not_principal" in self.form.cleaned_data.get("principal", [])
            ),
        ]
        facets.append(Facet("Principal", "principal", "checkbox", items))

    def facet_stub(self, facets, qs):
        qs = self.form.filter_queryset(qs, exclude="stub")
        counts = qs.aggregate(
            stub_counts=Count("pk", filter=Q(stub=True), distinct=True),
            not_stub_counts=Count("pk", filter=Q(stub=False), distinct=True),
        )
        items = [
            FacetItem(
                "Stub",
                "stub",
                counts.get("stub_counts", 0),
                "stub" in self.form.cleaned_data.get("stub", [])
            ),
            FacetItem(
                "Not a stub",
                "not_stub",
                counts.get("not_stub_counts", 0),
                "not_stub" in self.form.cleaned_data.get("stub", [])
            ),
        ]
        facets.append(Facet("Stubs", "stub", "checkbox", items))

    def facet_tasks(self, facets, qs):
        qs = self.form.filter_queryset(qs, exclude="tasks")
        task_states = qs.annotate(
            has_open_states=Count(
                Case(When(tasks__state__in=Task.OPEN_STATES, then=Value(1)), output_field=IntegerField())),
            has_unblocked_states=Count(
                Case(When(tasks__state__in=Task.UNBLOCKED_STATES, then=Value(1)), output_field=IntegerField())),
            has_blocked_states=Count(
                Case(When(tasks__state=Task.BLOCKED, then=Value(1)), output_field=IntegerField())),
        ).values('has_open_states', 'has_unblocked_states', 'has_blocked_states')

        # Organize the results into totals per state
        counts = {'open_states': 0, 'unblocked_states': 0, 'only_blocked_states': 0, 'no_open_states': 0}

        for item in task_states:
            if item['has_open_states'] > 0:
                counts['open_states'] += 1
            else:
                counts['no_open_states'] += 1

            # unblocked and only blocked tasks
            if item['has_unblocked_states'] > 0:
                counts['unblocked_states'] += 1
            if item['has_blocked_states'] > 0 and not item['has_unblocked_states'] > 0:
                counts['only_blocked_states'] += 1

        items = [
            FacetItem(
                "Has open tasks",
                "has_open_tasks",
                counts['open_states'],
                "has_open_tasks" in self.form.cleaned_data.get("tasks", [])
            ),
            FacetItem(
                "Has unblocked tasks",
                "has_unblocked_tasks",
                counts['unblocked_states'],
                "has_unblocked_tasks" in self.form.cleaned_data.get("tasks", [])
            ),
            FacetItem(
                "Has only blocked tasks",
                "has_only_blocked_tasks",
                counts['only_blocked_states'],
                "has_only_blocked_tasks" in self.form.cleaned_data.get("tasks", [])
            ),
            FacetItem(
                "Has no open tasks",
                "no_open_tasks",
                counts['no_open_states'],
                "no_open_tasks" in self.form.cleaned_data.get("tasks", [])
            ),
        ]
        facets.append(Facet("Tasks", "tasks", "checkbox", items))

    def facet_primary(self, facets, qs):
        qs = self.form.filter_queryset(qs, exclude="primary")
        counts = qs.aggregate(
            primary_counts=Count("pk", filter=Q(parent_work__isnull=True), distinct=True),
            subsidiary_counts=Count("pk", filter=Q(parent_work__isnull=False), distinct=True),
        )
        items = [
            FacetItem(
                "Primary",
                "primary",
                counts.get("primary_counts", 0),
                "primary" in self.form.cleaned_data.get("primary", [])
            ),
            FacetItem(
                "Subsidiary",
                "subsidiary",
                counts.get("subsidiary_counts", 0),
                "subsidiary" in self.form.cleaned_data.get("primary", [])
            ),
        ]
        facets.append(Facet("Primary and Subsidiary", "primary", "checkbox", items))

    def facet_commencement(self, facets, qs):
        qs = self.form.filter_queryset(qs, exclude="commencement")
        counts = qs.aggregate(
            commenced_count=Count("pk", filter=Q(commenced=True), distinct=True),
            not_commenced_count=Count("pk", filter=Q(commenced=False), distinct=True),
            date_unknown_count=Count("pk", filter=Q(commencements__date__isnull=True, commenced=True), distinct=True),
        )
        qs = qs.annotate(Count("commencements"))
        counts['multipe_count'] = qs.filter(commencements__count__gt=1).count()
        items = [
            FacetItem(
                "Commenced",
                "yes",
                counts.get("commenced_count", 0),
                "yes" in self.form.cleaned_data.get("commencement", [])
            ),
            FacetItem(
                "Not commenced",
                "no",
                counts.get("not_commenced_count", 0),
                "no" in self.form.cleaned_data.get("commencement", [])
            ),
            FacetItem(
                "Commencement date unknown",
                "date_unknown",
                counts.get("date_unknown_count", 0),
                "date_unknown" in self.form.cleaned_data.get("commencement", [])
            ),
            FacetItem(
                "Multiple commencements",
                "multiple",
                counts.get("multipe_count", 0),
                "multiple" in self.form.cleaned_data.get("commencement", [])
            ),
        ]
        facets.append(Facet("Commencements", "commencement", "checkbox", items))

    def facet_amendment(self, facet, qs):
        qs = self.form.filter_queryset(qs, exclude="amendment")
        counts = qs.aggregate(
            amended_count=Count("pk", filter=Q(amendments__isnull=False), distinct=True),
            not_amended_count=Count("pk", filter=Q(amendments__isnull=True), distinct=True),
        )
        items = [
            FacetItem(
                "Amended",
                "yes",
                counts.get("amended_count", 0),
                "yes" in self.form.cleaned_data.get("amendment", [])
            ),
            FacetItem(
                "Not amended",
                "no",
                counts.get("not_amended_count", 0),
                "no" in self.form.cleaned_data.get("amendment", [])
            ),
        ]
        facet.append(Facet("Amendments", "amendment", "checkbox", items))

    def facet_consolidation(self, facets,  qs):
        qs = self.form.filter_queryset(qs, exclude="consolidation")
        counts = qs.aggregate(
            has_consolidation=Count("pk", filter=Q(arbitrary_expression_dates__date__isnull=False), distinct=True),
            no_consolidation=Count("pk", filter=Q(arbitrary_expression_dates__date__isnull=True), distinct=True),
        )
        items = [
            FacetItem(
                "Has consolidation",
                "has_consolidation",
                counts.get("has_consolidation", 0),
                "has_consolidation" in self.form.cleaned_data.get("consolidation", [])
            ),
            FacetItem(
                "No consolidation",
                "no_consolidation",
                counts.get("no_consolidation", 0),
                "no_consolidation" in self.form.cleaned_data.get("consolidation", [])
            ),
        ]
        facets.append(Facet("Consolidations", "consolidation", "checkbox", items))

    def facet_publication_document(self, facets,  qs):
        qs = self.form.filter_queryset(qs, exclude="publication_document")
        counts = qs.aggregate(
            has_publication_document=Count("pk", filter=Q(publication_document__isnull=False), distinct=True),
            no_publication_document=Count("pk", filter=Q(publication_document__isnull=True), distinct=True),
        )
        items = [
            FacetItem(
                "Has publication document",
                "has_publication_document",
                counts.get("has_publication_document", 0),
                "has_publication_document" in self.form.cleaned_data.get("publication_document", [])
            ),
            FacetItem(
                "No publication document",
                "no_publication_document",
                counts.get("no_publication_document", 0),
                "no_publication_document" in self.form.cleaned_data.get("publication_document", [])
            ),
        ]
        facets.append(Facet("Publication document", "publication_document", "checkbox", items))

    def facet_repeal(self, facets, qs):
        qs = self.form.filter_queryset(qs, exclude="repeal")
        counts = qs.aggregate(
            repealed_count=Count("pk", filter=Q(repealed_date__isnull=False), distinct=True),
            not_repealed_count=Count("pk", filter=Q(repealed_date__isnull=True), distinct=True),
        )
        items = [
            FacetItem(
                "Repealed",
                "yes",
                counts.get("repealed_count", 0),
                "yes" in self.form.cleaned_data.get("repeal", [])
            ),
            FacetItem(
                "Not repealed",
                "no",
                counts.get("not_repealed_count", 0),
                "no" in self.form.cleaned_data.get("repeal", [])
            ),
        ]
        facets.append(Facet("Repeals", "repeal", "checkbox", items))

    def facet_points_in_time(self, facets, qs):
        qs = self.form.filter_queryset(qs, exclude="documents")
        no_document_ids = qs.filter(document__isnull=True).values_list('pk', flat=True)
        deleted_document_ids = qs.filter(document__deleted=True).values_list('pk', flat=True)
        undeleted_document_ids = qs.filter(document__deleted=False).values_list('pk', flat=True)
        all_deleted_document_ids = deleted_document_ids.exclude(id__in=undeleted_document_ids)
        no_document_ids = list(no_document_ids) + list(all_deleted_document_ids)
        items = [
            FacetItem(
                "Has no points in time",
                "none",
                qs.annotate(Count('document')).filter(id__in=no_document_ids).count(),
                "none" in self.form.cleaned_data.get("documents", [])
            ),
            FacetItem(
                "Has one point in time",
                "one",
                qs.filter(document__deleted=False).annotate(Count('document')).filter(document__count=1).count(),
                "one" in self.form.cleaned_data.get("documents", [])
            ),
            FacetItem(
                "Has multiple points in time",
                "multiple",
                qs.filter(document__deleted=False).annotate(Count('document')).filter(document__count__gt=1).count(),
                "multiple" in self.form.cleaned_data.get("documents", [])
            ),
        ]
        facets.append(Facet("Points in time", "documents", "checkbox", items))

    def facet_point_in_time_status(self, facets, qs):
        qs = self.form.filter_queryset(qs, exclude="status")
        counts = qs.aggregate(
            drafts_count=Count("pk", filter=Q(document__draft=True), distinct=True),
            published_count=Count("pk", filter=Q(document__draft=False), distinct=True),
        )
        items = [
            FacetItem(
                "Draft",
                "draft",
                counts.get("drafts_count", 0),
                "draft" in self.form.cleaned_data.get("status", [])
            ),
            FacetItem(
                "Published",
                "published",
                counts.get("published_count", 0),
                "published" in self.form.cleaned_data.get("status", [])
            ),
        ]
        facets.append(Facet("Point in time status", "status", "checkbox",  items))

    def facet_taxonomy(self, taxonomy_tree, qs):
        qs = self.form.filter_queryset(qs, exclude="taxonomy_topic")
        # count works per taxonomy topic
        counts = {
            x["taxonomy_topics__slug"]: x["count"]
            for x in qs.values("taxonomy_topics__slug").annotate(count=Count("taxonomy_topics__slug")).order_by()
        }

        # fold the counts into the taxonomy tree
        def decorate(item):
            total = 0
            for child in item.get('children', []):
                total = total + decorate(child)
            # count for this item
            item['data']['count'] = counts.get(item["data"]["slug"])
            # total of count for descendants
            item['data']['total'] = total
            return total + (item['data']['count'] or 0)

        for item in taxonomy_tree:
            decorate(item)


class WorkActionsView(PlaceViewBase, FormView):
    form_class = WorkBulkActionsForm
    template_name = "indigo_app/place/_works_actions.html"

    def form_valid(self, form):
        if form.cleaned_data['save']:
            form.save_changes()
            messages.success(self.request, f"Updated {form.cleaned_data['works'].count()} works.")
            return redirect(
                self.request.META.get('HTTP_REFERER')
                or reverse('place_works', kwargs={'place': self.kwargs['place']})
            )
        else:
            return self.form_invalid(form)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(**kwargs)

        # get the union of all the work's taxonomy topics
        if form.cleaned_data.get('works'):
            context["taxonomy_topics"] = TaxonomyTopic.objects.filter(works__in=form.cleaned_data["works"]).distinct()

        if form.is_valid:
            context["works"] = form.cleaned_data.get("works", [])

        return context


class WorkDetailView(PlaceViewBase, DetailView):
    template_name = 'indigo_app/place/_work_detail.html'
    queryset = Work.objects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        work = self.object

        context["overview_data"] = self.get_overview_data()
        context["tab"] = "overview"

        # count documents
        context["n_documents"] = Document.objects.undeleted().filter(work=work).count()

        # count commencements
        context["n_commencements"] = work.commencements.count()
        context["n_commencements_made"] = work.commencements_made.count()

        # count amendments
        context["n_amendments"] = work.amendments.count()
        context["n_amendments_made"] = work.amendments_made.count()

        # count repeals
        context["n_repeals"] = 1 if work.repealed_by else 0
        context["n_repeals_made"] = work.repealed_works.count()

        # count primary / subsidiary works
        context["n_primary_works"] = 1 if work.parent_work else 0
        context["n_subsidiary_works"] = work.child_works.count()

        # count tasks
        context["n_tasks"] = work.tasks.filter(state__in=Task.OPEN_STATES).count()

        return context

    def get_overview_data(self):
        """ Return overview data for the work as a list of OverviewDataEntry objects"""
        # TODO: are the translations being done correctly here?
        # TODO: turn this into a form; overview_data will fall away
        def format_date(date_obj):
            return date_obj.strftime("%Y-%m-%d")

        work = self.object

        # properties, e.g. Chapter number
        overview_data = [
            OverviewDataEntry(_(prop["label"]), prop["value"]) for prop in work.labeled_properties()
        ]

        publication = describe_publication_event(work, friendly_date=False, placeholder=hasattr(work, 'publication_document'))
        if publication:
            overview_data.append(OverviewDataEntry(_("Publication"), _(publication.description)))

        if work.assent_date:
            overview_data.append(OverviewDataEntry(_("Assent date"), format_date(work.assent_date)))

        as_at_date = work.as_at_date()
        if as_at_date:
            overview_data.append(OverviewDataEntry(_("As-at date"), format_date(as_at_date),
                                                   overridden=work.as_at_date_override))

        for consolidation in work.arbitrary_expression_dates.all():
            overview_data.append(OverviewDataEntry(_("Consolidation date"), format_date(consolidation.date)))

        consolidation_note = work.consolidation_note()
        if consolidation_note:
            overview_data.append(OverviewDataEntry(_("Consolidation note"), _(consolidation_note),
                                                   overridden=work.consolidation_note_override))

        if work.disclaimer:
            overview_data.append(OverviewDataEntry(_("Disclaimer"), _(work.disclaimer)))

        return overview_data


class WorkDocumentsView(PlaceViewBase, DetailView):
    template_name = 'indigo_app/place/_work_detail_documents.html'
    model = Work

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['documents'] = Document.objects.no_xml().undeleted().filter(work=self.object).order_by('-expression_date', 'language')

        return context


class WorkCommencementsView(PlaceViewBase, DetailView):
    template_name = 'indigo_api/_work_commencement_tables.html'
    queryset = Work.objects.prefetch_related(
        'commencements', 'commencements__commenced_work', 'commencements__commencing_work'
    )


class WorkAmendmentsView(PlaceViewBase, DetailView):
    template_name = 'indigo_api/_work_amendment_tables.html'
    queryset = Work.objects.prefetch_related(
        'amendments', 'amendments__amended_work', 'amendments__amending_work'
    )


class WorkRepealsView(PlaceViewBase, DetailView):
    template_name = 'indigo_api/_work_repeal_tables.html'
    model = Work


class WorkSubsidiaryView(PlaceViewBase, DetailView):
    template_name = 'indigo_api/_work_subsidiary_tables.html'
    model = Work


class WorkTasksView(PlaceViewBase, DetailView):
    template_name = 'indigo_api/_task_cards.html'
    model = Work

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tasks = self.object.tasks.filter(state__in=Task.OPEN_STATES)
        context['task_groups'] = Task.task_columns(['blocked', 'open', 'assigned', 'pending_review'], tasks)

        return context
