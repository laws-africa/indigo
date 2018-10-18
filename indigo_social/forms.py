# -*- coding: utf-8 -*-
from django import forms
from allauth.utils import generate_unique_username

from indigo_api.models import Country
from indigo_social.models import UserProfile
from indigo_social.badges import badges


class UserProfileForm(forms.ModelForm):

    first_name = forms.CharField(label='First name')
    last_name = forms.CharField(label='Last name')
    username = forms.CharField(label='Username')
    country = forms.ModelChoiceField(required=True, queryset=Country.objects, label='Country', empty_label=None)

    class Meta:
        model = UserProfile
        fields = (
            # personal info (also includes first_name and last_name)
            'profile_photo',
            'bio',
            # work
            'organisations',
            'skills',
            'qualifications',
            'specialisations',
            'areas_of_law',
            # social
            'twitter_username',
            'linkedin_profile',
        )

    def clean_twitter_username(self):
        if self.cleaned_data['twitter_username']:
            twitter_username = self.cleaned_data['twitter_username'].strip('@')
            return twitter_username

    def clean_username(self):
        if self.cleaned_data['username']:
            return generate_unique_username([self.cleaned_data['username']])

    def save(self, commit=True):
        super(UserProfileForm, self).save()
        self.instance.user.first_name = self.cleaned_data['first_name']
        self.instance.user.last_name = self.cleaned_data['last_name']
        self.instance.user.username = self.cleaned_data['username']
        self.instance.user.editor.country = self.cleaned_data['country']
        self.instance.user.editor.save()
        self.instance.user.save()


def badge_choices():
    return sorted([(b.slug, u'%s – %s' % (b.name, b.description)) for b in badges.registry.itervalues()])


class AwardBadgeForm(forms.Form):
    badge = forms.ChoiceField(choices=badge_choices)
    next = forms.CharField(required=False)

    def actual_badge(self):
        return badges.registry.get(self.cleaned_data.get('badge'))
