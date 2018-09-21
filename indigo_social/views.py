# coding=utf-8
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView, UpdateView

from .forms import UserProfileForm
from .models import UserProfile


class ContributorsView(ListView):
    model = UserProfile
    template_name = 'indigo_social/contributors.html'

    def get_context_data(self, **kwargs):
        context = super(ContributorsView, self).get_context_data(**kwargs)
        context['profiles_plus_initials'] = [
            {
                'id': x.id,
                'first_name': x.user.first_name,
                'initial': x.user.last_name[0] + '.' if x.user.last_name else '',
                'organisations': x.organisations,
                'bio': x.bio
            }
            for x in context['userprofile_list']
        ]
        return context


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
        return ''
