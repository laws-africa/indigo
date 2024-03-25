import logging
from collections import Counter
from dataclasses import dataclass
from datetime import timedelta

from actstream import action
from actstream.models import Action
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Subquery, IntegerField, OuterRef
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, TemplateView, UpdateView, FormView, DetailView
from django.views.generic.list import MultipleObjectMixin
from django_htmx.http import push_url
from lxml import etree

from indigo_api.models import Country, Task, Work, Subtype, Locality, TaskLabel, Document, TaxonomyTopic, AllPlace
from indigo_api.timeline import describe_publication_event
from indigo_app.forms import WorkFilterForm, PlaceSettingsForm, PlaceUsersForm, ExplorerForm, WorkBulkActionsForm, \
    WorkChooserForm, WorkBulkUpdateForm, WorkBulkApproveForm, WorkBulkUnapproveForm
from indigo_app.xlsx_exporter import XlsxExporter
from indigo_social.badges import badges
from .base import AbstractAuthedIndigoView, PlaceViewBase, PlaceWorksViewBase

log = logging.getLogger(__name__)


@dataclass
class OverviewDataEntry:
    key: str
    value: str
    overridden: bool = False


def get_work_overview_data(work):
    """ Return overview data for the work as a list of OverviewDataEntry objects"""
    def format_date(date_obj):
        return date_obj.strftime("%Y-%m-%d")

    overview_data = []

    publication = describe_publication_event(work, friendly_date=False,
                                             placeholder=hasattr(work, 'publication_document'))
    if publication:
        overview_data.append(OverviewDataEntry(_("Publication"), _(publication.description)))

    if work.assent_date:
        overview_data.append(OverviewDataEntry(_("Assent date"), format_date(work.assent_date)))

    if work.commencement_date:
        overview_data.append(OverviewDataEntry(_("Commenced"), format_date(work.commencement_date)))

    if work.repealed_date:
        overview_data.append(OverviewDataEntry(_("Repealed"), format_date(work.repealed_date)))

    # properties, e.g. Chapter number
    for prop in work.labeled_properties():
        overview_data.append(OverviewDataEntry(_(prop["label"]), prop["value"]))

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

    if work.principal:
        overview_data.append(OverviewDataEntry(_("Principal"), _(
            "Principal works are not simply repeals, amendments or commencements, and should have full text content.")))

    return overview_data


class PlaceListView(AbstractAuthedIndigoView, TemplateView):
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
            .all()

        for c in context['countries']:
            # ensure zeroes
            c.n_works = c.n_works or 0

        return context


class PlaceDetailView(PlaceViewBase, TemplateView):
    template_name = 'place/detail.html'
    tab = 'overview'
    allow_all_place = True

    def get(self, request, *args, **kwargs):
        if self.place.place_code == 'all':
            return redirect('place_works', place='all')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        works = Work.objects.filter(country=self.country, locality=self.locality) \
            .order_by('-updated_at')

        context['recently_updated_works'] = self.get_recently_updated_works()
        context['recently_created_works'] = self.get_recently_created_works()
        context['subtypes'] = self.get_works_by_subtype(works)
        context['total_works'] = sum(p[1] for p in context['subtypes'])

        # open tasks
        open_tasks_data = self.calculate_open_tasks()
        context['open_tasks'] = open_tasks_data['open_tasks_chart']
        context['open_tasks_by_label'] = open_tasks_data['labels_chart']
        context['total_open_tasks'] = open_tasks_data['total_open_tasks']

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
                'state_string': _('Open'),
                'count': open_tasks,
                'percentage': int((open_tasks / (total_open_tasks or 1)) * 100)
            },
            {
                'state': 'assigned',
                'state_string': _('Assigned'),
                'count': assigned_tasks,
                'percentage': int((assigned_tasks / (total_open_tasks or 1)) * 100)
            },
            {
                'state': 'pending_review',
                'state_string': _('Pending review'),
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
            (_('List introductions containing remarks'), '//a:subsection//a:blockList/a:listIntroduction/a:remark', '2'),
            (_('Adjacent block lists'), '//a:blockList/following-sibling::*[1][self::a:blockList]', '1'),
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
            raise ValueError(_("Expression must produce elements, but found %(classname)s instead.") %
                             {"classname": e.__class__.__name__})

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

        messages.success(self.request, _("Settings updated."))

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
        messages.success(self.request, _("Users updated."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('place_users', kwargs={'place': self.kwargs['place']})


class PlaceWorksIndexView(PlaceWorksViewBase, TemplateView):
    tab = 'place_settings'
    permission_required = ('indigo_api.change_placesettings',)

    def get(self, request, *args, **kwargs):
        works = self.get_base_queryset().order_by('publication_date')
        filename = _("Full index for %(place)s.xlsx") % {"place": self.place}
        exporter = XlsxExporter(self.country, self.locality)
        return exporter.generate_xlsx(works, filename, True)


class PlaceLocalitiesView(PlaceViewBase, TemplateView):
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
            .all()

        return context


class PlaceWorksView(PlaceWorksViewBase, ListView):
    template_name = 'indigo_app/place/works.html'
    tab = 'works'
    context_object_name = 'works'
    paginate_by = 50
    http_method_names = ['post', 'get']
    filter_form_class = WorkFilterForm
    allow_all_place = True

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.form = self.filter_form_class(self.country, request.POST or request.GET)
        self.form.is_valid()

        if self.form.data.get('format') == 'xlsx':
            exporter = XlsxExporter(self.country, self.locality)
            filename = _("legislation %(place)s.xlsx") % {"place": self.kwargs['place']}
            return exporter.generate_xlsx(self.get_queryset(), filename, False)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.form.filter_queryset(self.get_base_queryset())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        # using .only("pk") makes the query much faster; values_list just gives us the pks
        work_pks_list = list(self.get_queryset().only("pk").values_list("pk", flat=True))
        context['work_pks'] = ' '.join(str(pk) for pk in work_pks_list)
        context['total_works'] = self.get_base_queryset().count()
        query_url = (self.request.POST or self.request.GET).urlencode()
        context['facets_url'] = (
            reverse('place_works_facets', kwargs={'place': self.kwargs['place']}) +
            '?' + query_url
        )
        if self.country.place_code != 'all':
            context['download_xsl_url'] = (
                reverse('place_works', kwargs={'place': self.kwargs['place']}) +
                '?' + query_url + '&format=xlsx'
            )
        return context

    def render_to_response(self, context, **response_kwargs):
        resp = super().render_to_response(context, **response_kwargs)
        if self.request.htmx:
            # encode request.POST as a URL string
            url = f"{self.request.path}?{self.form.data_as_url()}"
            resp = push_url(resp, url)
        return resp

    def get_template_names(self):
        if self.request.htmx:
            return ['indigo_app/place/_works_list.html']
        return super().get_template_names()

    def has_all_country_permission(self):
        return True


class PlaceWorksFacetsView(PlaceWorksViewBase, TemplateView):
    template_name = 'indigo_app/place/_works_facets.html'
    allow_all_place = True

    def get(self, request, *args, **kwargs):
        self.form = PlaceWorksView.filter_form_class(self.country, request.GET)
        self.form.is_valid()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['form'] = self.form
        context['taxonomy_toc'] = TaxonomyTopic.get_toc_tree(self.request.GET, all_topics=False)

        if self.country.place_code == 'all':
            # dump the places tree for the places the user has permissions for
            if self.request.user.is_superuser:
                countries = Country.objects
            else:
                countries = self.request.user.editor.permitted_countries.all()
            countries = countries.prefetch_related('country', 'localities')
            context['places_toc'] = [{
                'title': country.name,
                'data': {
                    'slug': country.code,
                    'count': 0,
                    'total': 0,
                },
                'children': [{
                    'title': loc.name,
                    'data': {
                        'slug': loc.place_code,
                        'count': 0,
                        'total': 0,
                    },
                    'children': [],
                } for loc in country.localities.all()]
            } for country in countries]

        qs = self.get_base_queryset()

        # build facets
        context["work_facets"] = self.form.work_facets(qs, context['taxonomy_toc'], context.get('places_toc', []))
        context["document_facets"] = self.form.document_facets(qs)

        return context


class WorkActionsView(PlaceWorksViewBase, FormView):
    form_class = WorkBulkActionsForm
    template_name = "indigo_app/place/_works_actions.html"
    allow_all_place = True

    def form_valid(self, form):
        # this form just gets the works and gives the context to the actions toolbar
        return self.form_invalid(form)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.has_perm('indigo_api.bulk_add_work'):
            works, disallowed = self.get_works(form)
            context["works"] = works
            context["works_in_progress"] = works.filter(work_in_progress=True) if works else []
            context["approved_works"] = works.filter(work_in_progress=False) if works else []
            context["n_disallowed"] = disallowed
        return context

    def has_all_country_permission(self):
        # we'll double check permissions elsewhere
        return True

    def get_works(self, form):
        if form.cleaned_data.get("all_work_pks"):
            works = self.get_base_queryset().filter(pk__in=form.cleaned_data.get("all_work_pks"))
        else:
            works = form.cleaned_data.get("works", self.get_base_queryset().none())

        disallowed = 0
        if self.country.place_code == 'all':
            # restrict to those places that the user has perms for
            n_works = works.count()
            works = AllPlace.filter_works_queryset(works, self.request.user)
            disallowed = n_works - works.count()

        return works, disallowed


class WorkBulkActionBase(PlaceViewBase, FormView):
    """Base view for bulk actions on works. Ensures permissions for the "all" country, and passes
    place information to the form. Assumes the form class extends WorkBulkActionFormBase.
    """
    allow_all_place = True

    def has_all_country_permission(self):
        # the forms must filter the works to the countries for which the user has permissions
        return True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['country'] = self.country
        kwargs['locality'] = self.locality
        kwargs['user'] = self.request.user
        return kwargs


class WorkBulkUpdateView(WorkBulkActionBase):
    form_class = WorkBulkUpdateForm
    template_name = "indigo_app/place/_bulk_update_form.html"
    permission_required = ('indigo_api.view_country', 'indigo_api.change_work')

    def form_valid(self, form):
        if form.cleaned_data['save']:
            form.save_changes()
            messages.success(self.request, _("Updated %(works_count)s works.") % {"works_count": form.cleaned_data['works'].count()})
            return redirect(self.request.headers["Referer"])
        return self.form_invalid(form)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(**kwargs)
        works = form.cleaned_data.get("works")
        context["works"] = works
        # get the union of all the works' taxonomy topics
        context["taxonomy_topics"] = TaxonomyTopic.objects.filter(works__in=works).distinct()
        return context


class WorkBulkApproveView(WorkBulkActionBase):
    form_class = WorkBulkApproveForm
    template_name = "indigo_app/place/_bulk_approve_form.html"
    permission_required = ('indigo_api.view_country', 'indigo_api.bulk_add_work')

    def form_valid(self, form):
        if form.cleaned_data.get("approve"):
            form.save_changes(self.request)
            self.send_success_messages(form)
            return redirect(self.request.headers["Referer"])
        return self.form_invalid(form)

    def send_success_messages(self, form):
        messages.success(self.request, _("Approved %(works_count)s works.") % {"works_count": form.broker.works.count()})
        if form.broker.import_tasks:
            messages.success(self.request, _("Created %(import_tasks_count)s Import tasks.") % {"import_tasks_count": len(form.broker.import_tasks)})
        if form.broker.gazette_tasks:
            messages.success(self.request, _("Created %(gazette_tasks_count)s Gazette tasks.") % {"gazette_tasks_count": len(form.broker.gazette_tasks)})
        if form.broker.amendment_tasks:
            messages.success(self.request, _("Created %(amendment_tasks_count)s Amendment tasks.") % {"amendment_tasks_count": len(form.broker.amendment_tasks)})


class WorkBulkUnapproveView(WorkBulkActionBase):
    form_class = WorkBulkUnapproveForm
    template_name = "indigo_app/place/_bulk_unapprove_form.html"
    permission_required = ('indigo_api.view_country', 'indigo_api.bulk_add_work')

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(**kwargs)
        context["works"] = form.cleaned_data.get("works").order_by("-created_at")
        return context

    def form_valid(self, form):
        if form.cleaned_data.get("unapprove"):
            for work in form.cleaned_data["works"]:
                work.unapprove(self.request.user)
            messages.success(self.request, _("Unapproved %(works_count)s works.") % {"works_count": form.cleaned_data['works'].count()})
            return redirect(self.request.headers["Referer"])
        return self.form_invalid(form)


class WorkChooserView(PlaceViewBase, ListView):
    """This renders the filter form and the first page of results for the work chooser modal.
    HTMX reloads this view when filtering criteria are changed.
    """
    template_name = 'indigo_app/place/_work_chooser.html'
    model = Work
    paginate_by = 25

    http_method_names = ['get', 'post']

    def post(self, request, *args, **kwargs):
        # treat POST as GET
        return self.get(request, *args, **kwargs)

    def get_queryset(self):
        data = (self.request.POST or self.request.GET).copy()
        if 'country' not in data:
            data['country'] = self.country.pk
            if 'locality' not in data and self.locality:
                data['locality'] = self.locality.pk
        self.form = WorkChooserForm(data)
        self.form.is_valid()

        return self.form.filter_queryset(super().get_queryset())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["form"] = self.form
        # these are used when the final form is submitted
        context["work_field"] = self.form.data.get('field', 'work')
        context["hx_submit"] = self.form.data.get('submit')
        context["hx_target"] = self.form.data.get('target')
        context["hx_include"] = self.form.data.get('include', "")
        context["hx_method"] = self.form.data.get("method", "hx-get")

        return context


class WorkChooserListView(WorkChooserView):
    """This renders the list of results for the work chooser modal."""
    template_name = 'indigo_app/place/_work_chooser_list.html'


class WorkDetailView(PlaceViewBase, DetailView):
    template_name = 'indigo_app/place/_work_detail.html'
    queryset = Work.objects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        work = self.object

        context["overview_data"] = get_work_overview_data(self.object)
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


class WorkCommentsView(PlaceViewBase, DetailView):
    template_name = 'indigo_api/_work_comments.html'
    model = Work

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_to_id'] = f"work-{self.object.pk}-comments"
        return context
