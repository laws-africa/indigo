# coding=utf-8
from datetime import timedelta

from actstream.models import Action
from django.views.generic import DetailView, ListView, UpdateView, TemplateView, FormView
from django.views.generic.list import MultipleObjectMixin
from django.urls import reverse
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from allauth.account.utils import user_display
from pinax.badges.models import BadgeAward
from pinax.badges.registry import badges

from indigo_api.models import Country, User
from indigo_app.views.base import AbstractAuthedIndigoView
from indigo_app.views.tasks import UserTasksView as UserTasksBaseView
from .forms import UserProfileForm, AwardBadgeForm
from .models import UserProfile


class ContributorsView(ListView):
    model = UserProfile
    template_name = 'indigo_social/contributors.html'
    queryset = UserProfile.objects.prefetch_related('user').order_by('-user__last_login')


class UserProfileView(DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'indigo_social/user_profile.html'
    threshold = timedelta(seconds=3)

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)

        context['can_award'] = self.request.user.has_perm('auth.change_user')
        if context['can_award']:
            context['award_form'] = AwardBadgeForm(user=self.object)

        activity = self.object.actor_actions.all()[:20]
        context['activity_stream'] = self.coalesce_entries(activity)

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
                    # if yes, was the previous action also an addition on the same workflow?
                    prev = stream[i - 1]
                    if getattr(prev, 'verb', None) == 'added' \
                            and action.target_object_id == prev.target_object_id:
                        # if yes, did the two actions happen close together?
                        if prev.timestamp - action.timestamp < self.threshold:
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


class UserProfileEditView(AbstractAuthedIndigoView, UpdateView):
    authentication_required = True
    model = UserProfile
    template_name = 'indigo_app/user_account/edit.html'
    form_class = UserProfileForm
    check_country_perms = False

    def get_context_data(self, **kwargs):
        context = super(UserProfileEditView, self).get_context_data(**kwargs)
        context['countries'] = Country.objects.all()
        return context

    def get_initial(self):
        initial = super(UserProfileEditView, self).get_initial()
        initial['first_name'] = self.request.user.first_name
        initial['last_name'] = self.request.user.last_name
        initial['username'] = self.request.user.username
        initial['country'] = self.request.user.editor.country
        return initial

    def get_object(self, queryset=None):
        return UserProfile.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse('edit_account')


class UserActivityView(MultipleObjectMixin, DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'indigo_social/user_activity.html'
    object_list = None
    page_size = 30
    js_view = ''
    threshold = timedelta(seconds=3)

    def get_context_data(self, **kwargs):
        context = super(UserActivityView, self).get_context_data(**kwargs)

        activity = self.object.actor_actions.all()
        activity = self.coalesce_entries(activity)

        paginator, page, versions, is_paginated = self.paginate_queryset(activity, self.page_size)
        context.update({
            'paginator': paginator,
            'page': page,
            'is_paginated': is_paginated,
            'user': self.object,
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
                    # if yes, was the previous action also an addition on the same workflow?
                    prev = stream[i - 1]
                    if getattr(prev, 'verb', None) == 'added' \
                            and action.target_object_id == prev.target_object_id:
                        # if yes, did the two actions happen close together?
                        if prev.timestamp - action.timestamp < self.threshold:
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


class AwardBadgeView(AbstractAuthedIndigoView, DetailView, FormView):
    """ View to grant a user a new badge
    """
    http_method_names = ['post']
    form_class = AwardBadgeForm
    model = User
    permission_required = ('auth.change_user',)
    slug_field = 'username'
    slug_url_kwarg = 'username'
    check_country_perms = False

    def post(self, request, *args, **kwargs):
        self.user = self.object = self.get_object()
        return super(AwardBadgeView, self).post(request, *args, **kwargs)

    def get_success_url(self):
        url = reverse('indigo_social:user_profile', kwargs={'username': self.user.username})
        return self.form.cleaned_data.get('next', url) or url

    def form_valid(self, form):
        self.form = form
        user = self.user
        badge = form.actual_badge()

        if badge.can_award(user):
            badge.possibly_award(user=self.user)
            messages.success(self.request, '%s badge awarded to %s' % (badge.name, user_display(user)))
        else:
            messages.warning(self.request, '%s badge couldn\'t be awarded to %s' % (badge.name, user_display(user)))
        return super(AwardBadgeView, self).form_valid(form)

    def form_invalid(self, form):
        self.form = form
        return redirect(self.get_success_url())


class BadgeListView(TemplateView):
    template_name = 'indigo_social/badges.html'

    def get_context_data(self, **context):
        context['badges'] = sorted(badges.registry.values(), key=lambda b: b.name)
        return context


class BadgeDetailView(TemplateView):
    template_name = 'indigo_social/badge_detail.html'

    def dispatch(self, request, slug):
        badge = badges.registry.get(slug)
        if not badge:
            raise Http404
        self.badge = badge
        return super(BadgeDetailView, self).dispatch(request, slug=slug)

    def get_context_data(self, **context):
        context['badge'] = self.badge
        context['awards'] = BadgeAward.objects.filter(slug=self.badge.slug).order_by('-awarded_at')
        return context


class UserTasksView(UserTasksBaseView):
    authentication_required = False
    template_name = 'indigo_social/user_tasks.html'

    def get_context_data(self, **kwargs):
        context = super(UserTasksView, self).get_context_data(**kwargs)
        context['user'] = User.objects.get(username=kwargs['username'])
        return context


class UserPopupView(AbstractAuthedIndigoView, DetailView):
    model = User
    context_object_name = 'user'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'indigo_social/user_popup.html'
    queryset = User.objects
