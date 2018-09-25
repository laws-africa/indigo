# coding=utf-8
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView, UpdateView, TemplateView
from django.urls import reverse
from django.http import Http404

from pinax.badges.models import BadgeAward
from pinax.badges.registry import badges
from .forms import UserProfileForm
from .models import UserProfile


class ContributorsView(ListView):
    model = UserProfile
    template_name = 'indigo_social/contributors.html'
    queryset = UserProfile.objects.prefetch_related('user')


class UserProfileView(DetailView):
    model = UserProfile
    template_name = 'indigo_social/user_profile.html'

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        user_profile = UserProfile.objects.get(pk=str(self.kwargs['pk']))
        if user_profile.user.last_name:
            context['last_name_initial'] = user_profile.user.last_name[0] + '.'
        return context


class UserProfileEditView(UpdateView):
    model = UserProfile
    template_name = 'indigo_app/user_account/edit.html'
    form_class = UserProfileForm

    def get_initial(self):
        initial = super(UserProfileEditView, self).get_initial()
        initial['first_name'] = self.request.user.first_name
        initial['last_name'] = self.request.user.last_name
        return initial

    def get_object(self, queryset=None):
        return UserProfile.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse('edit_account')


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
