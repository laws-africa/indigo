# coding=utf-8
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView, UpdateView, TemplateView, FormView
from django.urls import reverse
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from allauth.account.utils import user_display
from pinax.badges.models import BadgeAward
from pinax.badges.registry import badges

from indigo_api.models import Country, User
from indigo_app.views.base import AbstractAuthedIndigoView
from .forms import UserProfileForm, AwardBadgeForm
from .models import UserProfile


class ContributorsView(ListView):
    model = UserProfile
    template_name = 'indigo_social/contributors.html'
    queryset = UserProfile.objects.prefetch_related('user')


class UserProfileView(DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'indigo_social/user_profile.html'

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)

        context['can_award'] = self.request.user.has_perm('auth.change_user')
        if context['can_award']:
            context['award_form'] = AwardBadgeForm()

        return context


class UserProfileEditView(AbstractAuthedIndigoView, UpdateView):
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
