# coding=utf-8
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView, UpdateView

from .models import UserProfile


class SocialHomeView(ListView):
    model = UserProfile
    template_name = 'indigo_social/social_home.html'

    def get_context_data(self, **kwargs):
        context = {
            'users': UserProfile.objects.all()
        }
        return context


class SocialProfileView(DetailView):
    model = UserProfile
    template_name = 'indigo_social/social_profile.html'


class SocialProfileEditView(UpdateView):
    model = UserProfile
    fields = [
        'bio',
    ]
    template_name = 'indigo_social/social_profile_edit.html'

    def get_object(self, queryset=None):
        return UserProfile.objects.get(user=self.request.user)

    def get_slug_field(self):
        pass

    def get_success_url(self):
        return 'edit'

