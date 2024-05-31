import datetime
import json
from itertools import chain

from actstream import action
from allauth.account.utils import user_display
from django import forms
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import BaseFormView
from django_comments.models import Comment
from django_fsm import has_transition_perm
from django_htmx.http import push_url

from indigo_api.models import Annotation, Task, TaskLabel, User, Work, TaxonomyTopic, TaskFile
from indigo_api.serializers import WorkSerializer
from indigo_api.views.attachments import view_attachment
from indigo_app.forms import TaskForm, TaskFilterForm, BulkTaskUpdateForm, TaskEditLabelsForm, BulkTaskStateChangeForm
from indigo_app.views.base import AbstractAuthedIndigoView, PlaceViewBase
from indigo_app.views.places import WorkChooserView


def task_file_response(task_file):
    """ Either return the task file as a response, or redirect to the URL.
    """
    if task_file.url:
        return redirect(task_file.url)
    return view_attachment(task_file)


class TaskViewBase(PlaceViewBase):
    tab = 'tasks'
    permission_required = ('indigo_api.view_task',)


class SingleTaskViewBase(TaskViewBase):
    model = Task

    def get_queryset(self):
        return super().get_queryset().filter(country=self.country, locality=self.locality)


class TaskListView(TaskViewBase, ListView):
    context_object_name = 'tasks'
    model = Task
    paginate_by = 50
    js_view = 'TaskListView TaskBulkUpdateView'

    def get(self, request, *args, **kwargs):
        self.form = TaskFilterForm(self.country, self.locality, request.GET)
        self.form.is_valid()

        return super().get(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        resp = super().render_to_response(context, **response_kwargs)
        if self.request.htmx:
            # encode request.POST as a URL string
            url = f"{self.request.path}?{self.form.data_as_url()}"
            resp = push_url(resp, url)
        return resp

    def get_template_names(self):
        if self.request.htmx:
            return ['indigo_api/_task_list.html']
        return super().get_template_names()

    def get_base_queryset(self):
        return Task.objects \
            .filter(country=self.country, locality=self.locality) \
            .select_related('document__language', 'document__language__language') \
            .defer('document__document_xml')

    def get_queryset(self):
        return self.form.filter_queryset(self.get_base_queryset())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_labels'] = TaskLabel.objects.all()
        context['form'] = self.form
        context['frbr_uri'] = self.request.GET.get('frbr_uri')
        context['total_tasks'] = self.get_base_queryset().count()
        if self.request.htmx:
            # don't show the place column
            context['place'] = False
            context['selectable'] = True

        context["taxonomy_toc"] = TaxonomyTopic.get_toc_tree(self.request.GET)
        context["work_facets"] = self.form.work_facets(self.form.works_queryset, context['taxonomy_toc'], [])
        context["task_facets"] = self.form.task_facets(self.get_base_queryset(), [])

        # warn when submitting task on behalf of another user
        Task.decorate_submission_message(context['tasks'], self)
        Task.decorate_permissions(context['tasks'], self.request.user)

        return context


class TaskDetailView(SingleTaskViewBase, DetailView):
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object

        # merge actions and comments
        actions = task.action_object_actions.all()
        task_content_type = ContentType.objects.get_for_model(self.model)
        comments = list(Comment.objects.filter(content_type=task_content_type, object_pk=task.id).select_related('user'))

        # get the annotation for the particular task
        try:
            task_annotation = task.annotation
        except Annotation.DoesNotExist:
            task_annotation = None

        # for the annotation that is linked to the task, get all the replies
        if task_annotation:
            # get the replies to the annotation
            annotation_replies = Annotation.objects.filter(in_reply_to=task_annotation)\
                    .select_related('created_by_user')

            comments.extend([Comment(user=a.created_by_user,
                                     comment=a.text,
                                     submit_date=a.created_at)
                            for a in annotation_replies])

        context['task_timeline'] = sorted(
            chain(comments, actions),
            key=lambda x: x.submit_date if hasattr(x, 'comment') else x.timestamp)

        # TODO: filter this to fewer tasks to not load too many tasks in the dropdown?
        context['possible_blocking_tasks'] = Task.objects.filter(country=task.country, locality=task.locality, state__in=Task.OPEN_STATES).all()
        context['blocked_by'] = task.blocked_by.all()

        # warn when submitting task on behalf of another user
        Task.decorate_submission_message([task], self)
        Task.decorate_permissions([task], self.request.user)

        # add work to context
        if task.work:
            context['work'] = task.work
            context['work_json'] = json.dumps(
                WorkSerializer(instance=task.work, context={'request': self.request}).data)

        # include labels form
        context['labels_form'] = TaskEditLabelsForm(instance=task)

        return context

    def get_template_names(self):
        if self.object.work:
            return ['indigo_api/work_task_detail.html']
        return super().get_template_names()


class TaskFileView(SingleTaskViewBase, DetailView):
    task_file = None

    def get(self, request, *args, **kwargs):
        task = self.get_object()
        try:
            if self.task_file == 'input_file':
                return task_file_response(task.input_file)
            return task_file_response(task.output_file)
        except TaskFile.DoesNotExist:
            pass
        raise Http404()


class TaskEditLabelsView(SingleTaskViewBase, UpdateView):
    form_class = TaskEditLabelsForm
    template_name = 'indigo_api/_task_labels.html'
    permission_required = ('indigo_api.change_task',)

    def form_valid(self, form):
        form.save()
        return self.form_invalid(form)


class TaskCreateView(TaskViewBase, CreateView):
    # permissions
    permission_required = ('indigo_api.add_task',)
    context_object_name = 'task'
    form_class = TaskForm
    model = Task

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        task = Task()
        task.country = self.country
        task.locality = self.locality
        task.created_by_user = self.request.user

        if self.request.GET.get('frbr_uri'):
            # pre-load a work
            try:
                work = Work.objects.get(frbr_uri=self.request.GET['frbr_uri'])
                if task.country == work.country and task.locality == work.locality:
                    task.work = work
            except Work.DoesNotExist:
                pass

        kwargs['instance'] = task
        kwargs['country'] = self.country
        kwargs['locality'] = self.locality
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task'] = context['form'].instance
        return context

    def get_success_url(self):
        return reverse('task_detail', kwargs={'place': self.kwargs['place'], 'pk': self.object.pk})


class TaskEditView(SingleTaskViewBase, UpdateView):
    # permissions
    permission_required = ('indigo_api.change_task',)
    context_object_name = 'task'
    form_class = TaskForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['country'] = self.country
        kwargs['locality'] = self.locality
        return kwargs

    def form_valid(self, form):
        task = self.object
        task.updated_by_user = self.request.user

        # action signals
        if form.changed_data:
            action.send(self.request.user, verb='updated', action_object=task, place_code=task.place.place_code)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('task_detail', kwargs={'place': self.kwargs['place'], 'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        user = self.request.user
        context['cancel_task_permission'] = has_transition_perm(task.cancel, user)
        context['block_task_permission'] = has_transition_perm(task.block, user)
        context['unblock_task_permission'] = has_transition_perm(task.unblock, user)
        return context


class TaskWorkChooserView(WorkChooserView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["disable_country"] = True
        context["disable_locality"] = True
        return context


class TaskFormWorkView(PlaceViewBase, TemplateView):
    template_name = 'indigo_api/_task_form_work.html'

    class Form(forms.ModelForm):
        class Meta:
            model = Task
            fields = ('work', 'document')

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.full_clean()
            work = self.cleaned_data.get('work')
            if work:
                self.fields['document'].queryset = work.expressions()
                self.fields['document'].choices = [('', _('None'))] + [(document.pk, f'{document.expression_date} · {document.language.code} – {document.title}') for document in self.fields['document'].queryset]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = Task(country=self.country, locality=self.locality)
        form = self.Form(self.request.GET, instance=task)
        form.is_valid()
        context['form'] = form
        context['task'] = form.instance
        return context


class PartialTaskFormView(PlaceViewBase, TemplateView):
    template_name = None

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = TaskForm(self.country, self.locality, self.request.POST)
        context["form"] = form
        return context


class TaskFormTitleView(PartialTaskFormView):
    template_name = 'indigo_api/_task_form_title.html'


class TaskFormTimelineDateView(PartialTaskFormView):
    template_name = 'indigo_api/_task_form_timeline_date.html'


class TaskFormInputFileView(PartialTaskFormView):
    template_name = 'indigo_api/_task_form_input_file.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context["form"].input_file_form
        return context


class TaskFormOutputFileView(PartialTaskFormView):
    template_name = 'indigo_api/_task_form_output_file.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context["form"].output_file_form
        return context


class TaskChangeStateView(SingleTaskViewBase, View, SingleObjectMixin):
    # permissions
    permission_required = ('indigo_api.change_task',)

    change = None
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        user = self.request.user
        task.updated_by_user = user
        task_content_type = ContentType.objects.get_for_model(task)
        comment_text = request.POST.get('comment', None)

        if task.customised:
            # redirect to custom close url, if necessary
            if self.change == 'close' and task.customised.close_url():
                return redirect(task.customised.close_url())

        for change, verb in Task.VERBS.items():
            if self.change == change:
                state_change = getattr(task, change)
                if not has_transition_perm(state_change, user):
                    raise PermissionDenied

                if comment_text:
                    comment = Comment(user=user, object_pk=task.id,
                                      user_name=user.get_full_name() or user.username,
                                      user_email=user.email,
                                      comment=comment_text,
                                      content_type=task_content_type,
                                      site_id=get_current_site(request).id)

                    state_change(user, comment=comment.comment)
                    # save the comment here so that it appears after the action
                    comment.submit_date = now()
                    comment.save()

                else:
                    state_change(user)

                if change == 'submit':
                    verb = _('submitted for review')
                if change == 'unsubmit':
                    verb = _('returned with changes requested')
                messages.success(request, _("Task '%(title)s' has been %(verb)s") % {"title": task.title, "verb": verb})

        task.save()

        return redirect(self.get_redirect_url())

    def get_redirect_url(self):
        if self.request.GET.get('next'):
            return self.request.GET.get('next')
        return reverse('task_detail', kwargs={'place': self.kwargs['place'], 'pk': self.kwargs['pk']})


class TaskAssignToView(SingleTaskViewBase, DetailView):
    template_name = "indigo_api/_task_assign_to_menu.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Task.decorate_potential_assignees([self.object], self.country, self.request.user)
        context["potential_assignees"] = self.object.potential_assignees
        context["show"] = True
        # prevent the form from being changed
        context["task"] = None
        return context


class TaskAssignView(SingleTaskViewBase, View, SingleObjectMixin):
    # permissions
    permission_required = ('indigo_api.change_task',)

    unassign = False
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        user = self.request.user

        if self.unassign:
            task.assign_to(None, user)
            messages.success(request, _("Task '%(title)s' has been unassigned") % {"title": task.title})
        else:
            assignee = User.objects.get(id=self.request.POST.get('assigned_to'))
            if not task.can_assign_to(assignee):
                raise PermissionDenied
            task.assign_to(assignee, user)
            if user == assignee:
                messages.success(request, _("You have picked up the task '%(title)s'") % {"title": task.title})
            else:
                messages.success(request, _("Task '%(title)s' has been assigned") % {"title": task.title})

        task.updated_by_user = user
        task.save()

        return redirect(self.get_redirect_url())

    def get_redirect_url(self):
        if self.request.GET.get('next'):
            return self.request.GET.get('next')
        return reverse('task_detail', kwargs={'place': self.kwargs['place'], 'pk': self.kwargs['pk']})


class TaskChangeBlockingTasksView(SingleTaskViewBase, View, SingleObjectMixin):
    # permissions
    permission_required = ('indigo_api.change_task',)

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        user = self.request.user
        task.updated_by_user = user
        ids = self.request.POST.getlist('blocked_by')

        if ids:
            blocked_by = Task.objects.filter(country=self.country, locality=self.locality, id__in=ids).all()
        else:
            blocked_by = []

        if blocked_by:
            if task.state == 'blocked':
                task.blocked_by.set(blocked_by)
                action.send(user, verb='updated', action_object=task,
                            place_code=task.place.place_code)
                messages.success(request, _("Task '%(title)s' has been updated") % {"title": task.title})

            elif has_transition_perm(task.block, user):
                task.blocked_by.set(blocked_by)
                task.block(user)
                messages.success(request, _("Task '%(title)s' has been blocked") % {"title": task.title})

        else:
            task.blocked_by.clear()
            if has_transition_perm(task.unblock, user):
                task.unblock(user)
                messages.success(request, _("Task '%(title)s' has been unblocked") % {"title": task.title})

        task.save()

        return redirect(self.get_redirect_url())

    def get_redirect_url(self):
        return reverse('task_detail', kwargs={'place': self.kwargs['place'], 'pk': self.kwargs['pk']})


class TaskBulkUpdateView(TaskViewBase, BaseFormView):
    """ Bulk update a set of tasks.
    """
    http_method_names = ['post']
    form_class = BulkTaskUpdateForm
    permission_required = ('indigo_api.change_task',)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['country'] = self.country
        return kwargs

    def form_valid(self, form):
        # TODO: add ability to bulk change state (specifically to `blocked`)
        assignee = form.cleaned_data.get('assigned_to')
        tasks = form.cleaned_data['tasks']
        count = 0

        for task in tasks:
            if task.is_open:
                if form.unassign or (assignee and task.can_assign_to(assignee)):
                    if task.assigned_to != assignee:
                        task.assign_to(assignee, self.request.user)
                        task.updated_by_user = self.request.user
                        task.save()
                        count += 1

        if count > 0:
            plural = 's' if count > 1 else ''
            if form.unassign:
                messages.success(self.request, _("Unassigned %(count)d task%(plural)s") % {"count": count, "plural": plural})
            elif assignee:
                messages.success(self.request, _("Assigned %(count)d task%(plural)s to %(user)s") % {"count": count, "plural": plural, "user": user_display(assignee)})

        return redirect(self.request.headers["Referer"])

    def form_invalid(self, form):
        messages.error(self.request, _("Computer says no."))
        return redirect(self.request.headers["Referer"])


class TaskBulkChangeStateView(TaskViewBase, BaseFormView):
    http_method_names = ['post']
    form_class = BulkTaskStateChangeForm
    permission_required = ('indigo_api.change_task',)
    change = None

    def form_valid(self, form):
        success_count = 0
        unsuccess_count = 0
        for task in form.cleaned_data['tasks']:
            state_change = getattr(task, self.change)
            if has_transition_perm(state_change, self.request.user):
                success_count += 1
                state_change(self.request.user)
            else:
                unsuccess_count += 1
        if success_count > 0:
            plural = 's' if success_count > 1 else ''
            messages.success(self.request, _("%(verb)s %(count)d task%(plural)s") %
                             {"verb": Task.VERBS[self.change], "count": success_count, "plural": plural})
        if unsuccess_count > 0:
            plural = 's' if unsuccess_count > 1 else ''
            messages.error(self.request, _("Couldn't %(verb)s %(count)d task%(plural)s")
                           % {"verb": self.change, "count": unsuccess_count, "plural": plural})

        return redirect(self.request.headers["Referer"])


class TaskBulkUnblockView(TaskBulkChangeStateView):
    change = 'unblock'


class TaskBulkBlockView(TaskBulkChangeStateView):
    change = 'block'


class UserTasksView(AbstractAuthedIndigoView, TemplateView):
    authentication_required = True
    template_name = 'indigo_app/tasks/my_tasks.html'
    tab = 'my_tasks'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs.get('username'):
            user = User.objects.get(username=kwargs['username'])
        else:
            user = self.request.user

        # open tasks assigned to this user
        context['open_assigned_tasks'] = Task.objects \
            .filter(assigned_to=user, state__in=Task.OPEN_STATES) \
            .all()

        # tasks previously assigned to this user and now pending approval
        context['tasks_pending_approval'] = Task.objects \
            .filter(submitted_by_user=user, state='pending_review') \
            .all()

        # tasks recently approved
        threshold = datetime.date.today() - datetime.timedelta(days=7)
        context['tasks_recently_approved'] = Task.objects \
            .filter(submitted_by_user=user, state='done') \
            .filter(updated_at__gte=threshold) \
            .all()[:50]

        context['tab_count'] = len(context['open_assigned_tasks']) + len(context['tasks_pending_approval'])

        return context


class AllTasksView(AbstractAuthedIndigoView, ListView):
    authentication_required = True
    template_name = 'indigo_app/tasks/all_tasks.html'
    context_object_name = 'tasks'
    paginate_by = 50
    paginate_orphans = 4
    tab = 'all_tasks'
    priority = False
    permission_required = ('indigo_api.view_task',)

    def get(self, request, *args, **kwargs):
        self.form = TaskFilterForm(None, None, request.GET)
        self.form.is_valid()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.form.filter_queryset(self.get_base_queryset())

    def get_base_queryset(self):
        return Task.objects \
            .filter(country__in=self.request.user.editor.permitted_countries.all()) \
            .select_related('document__language', 'document__language__language') \
            .defer('document__document_xml') \
            .order_by('-updated_at')

    def render_to_response(self, context, **response_kwargs):
        resp = super().render_to_response(context, **response_kwargs)
        if self.request.htmx:
            # encode request.POST as a URL string
            url = f"{self.request.path}?{self.form.data_as_url()}"
            resp = push_url(resp, url)
        return resp

    def get_template_names(self):
        if self.request.htmx:
            return ['indigo_api/_task_list.html']
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['form_url'] = reverse('all_tasks')
        context['tab_count'] = context['paginator'].count
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
        context['taxonomy_toc'] = TaxonomyTopic.get_toc_tree(self.request.GET)
        context["work_facets"] = self.form.work_facets(self.form.works_queryset, context['taxonomy_toc'], [])
        context["task_facets"] = self.form.task_facets(self.get_base_queryset(), context['places_toc'])
        context['total_tasks'] = self.get_base_queryset().count()
        context["hide_assigned_to"] = False
        context["place"] = True
        return context


class AvailableTasksView(AllTasksView):
    template_name = 'indigo_app/tasks/available_tasks.html'
    tab = 'available_tasks'

    def get_base_queryset(self):
        return super().get_base_queryset().filter(assigned_to=None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_url'] = reverse('available_tasks')
        context["hide_assigned_to"] = True
        return context


class TaskAssigneesView(TaskViewBase, TemplateView):
    http_method_names = ['post']
    template_name = 'indigo_api/_task_assign_to_menu.html'

    def post(self, request, *args, **kwargs):
        pks = request.POST.getlist('tasks', [])
        tasks = Task.objects.filter(pk__in=pks)
        users = []

        if tasks:
            Task.decorate_potential_assignees(tasks, self.country, self.request.user)
            # candidates are the intersection of all tasks
            users = set.intersection(*(set(t.potential_assignees) for t in tasks))
            users = sorted(users, key=lambda u: [u.first_name, u.last_name])

        return self.render_to_response({
            'potential_assignees': users,
            'unassign': 'unassign' in request.POST,
        })
