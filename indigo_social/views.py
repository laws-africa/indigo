# coding=utf-8
from __future__ import unicode_literals

from django.views.generic import TemplateView, UpdateView

from .models import UserProfile


class ISocialHome(TemplateView):
    template_name = 'indigo_social/isoc_home.html'


class ISocialProfile(UpdateView):
    model = UserProfile
    fields = [
        'bio',
    ]
    template_name = 'indigo_social/isoc_profile.html'

    # Generic detail view ISocialProfile must be called with either an object pk or a slug.
    def get_object(self, queryset=None):
        return UserProfile.objects.get(user=self.request.user)
