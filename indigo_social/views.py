from datetime import timedelta

from actstream.models import Action
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, TemplateView, FormView
from django.views.generic.list import MultipleObjectMixin
from django.urls import reverse
from django.http import Http404, FileResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.templatetags.static import static
from django.utils.translation import gettext as _
from allauth.account.utils import user_display

from indigo_api.models import Country, User
from indigo_app.views.base import AbstractAuthedIndigoView
from indigo_app.views.tasks import UserTasksView as UserTasksBaseView
from indigo_app.views.users import set_language_cookie
from .forms import UserProfileForm, AwardBadgeForm, UnawardBadgeForm
from .models import UserProfile, BadgeAward
from .badges import badges


class ContributorsView(AbstractAuthedIndigoView, ListView):
    model = UserProfile
    template_name = 'indigo_social/contributors.html'
    queryset = UserProfile.objects.prefetch_related('user').order_by('-user__last_login')


class UserProfileView(AbstractAuthedIndigoView, DetailView):
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
            context['unaward_form'] = UnawardBadgeForm(user=self.object)

        context['activity_stream'] = self.object.actor_actions.all()[:20]

        return context


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
        initial['language'] = self.request.user.editor.language
        return initial

    def get_object(self, queryset=None):
        return UserProfile.objects.get(user=self.request.user)

    def form_valid(self, form):
        resp = super().form_valid(form)
        set_language_cookie(resp, form.cleaned_data['language'])
        return resp

    def get_success_url(self):
        return reverse('edit_account')


class UserActivityView(AbstractAuthedIndigoView, MultipleObjectMixin, DetailView):
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

        paginator, page, versions, is_paginated = self.paginate_queryset(activity, self.page_size)
        context.update({
            'paginator': paginator,
            'page': page,
            'is_paginated': is_paginated,
            'user': self.object,
        })

        return context


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
            messages.success(self.request, _('%(badge)s badge awarded to %(user)s') % {'badge': badge.name, 'user': user_display(user)})
        else:
            messages.warning(self.request, _("%(badge)s badge couldn't be awarded to %(user)s") % {'badge': badge.name, 'user': user_display(user)})
        return super(AwardBadgeView, self).form_valid(form)

    def form_invalid(self, form):
        self.form = form
        return redirect(self.get_success_url())


class UnawardBadgeView(AwardBadgeView):
    form_class = UnawardBadgeForm

    def form_valid(self, form):
        self.form = form
        user = self.user
        badge = form.actual_badge()

        badge.unaward(user)
        messages.success(self.request, _('%(badge)s badge removed from %(user)s') % {'badge': badge.name, 'user': user_display(user)})
        return super(AwardBadgeView, self).form_valid(form)


class BadgeListView(AbstractAuthedIndigoView, TemplateView):
    template_name = 'indigo_social/badges.html'

    def get_context_data(self, **context):
        context['badges'] = sorted(badges.registry.values(), key=lambda b: b.name)
        return context


class BadgeDetailView(AbstractAuthedIndigoView, TemplateView):
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


class UserProfilePhotoView(AbstractAuthedIndigoView, View):
    def get(self, request, **kwargs):
        username = kwargs['username']
        nonce = kwargs['nonce']

        user = get_object_or_404(User, username=username)
        if not user.userprofile.profile_photo.name:
            return redirect(static('images/avatars/default_avatar.svg'))

        return FileResponse(user.userprofile.profile_photo)
