# coding=utf-8
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView, UpdateView

from .forms import UserProfileForm
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
        return ''
