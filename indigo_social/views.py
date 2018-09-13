# coding=utf-8
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.views.generic import TemplateView, UpdateView

from .forms import UserProfileForm
from .models import UserProfile


class ISocialHome(TemplateView):
    template_name = 'indigo_social/isoc_home.html'


class ISocialProfile(UpdateView):
    model = UserProfile
    template_name = 'indigo_social/isoc_profile.html'
    form_class = UserProfileForm

    def get_object(self, queryset=None):
        return User(pk=self.request.user.pk)
