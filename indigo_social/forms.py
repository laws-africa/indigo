from django import forms

from indigo_api.models import Country
from indigo_social.models import UserProfile


class UserProfileForm(forms.ModelForm):

    first_name = forms.CharField(label='First name')
    last_name = forms.CharField(label='Last name')
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

    def save(self, commit=True):
        super(UserProfileForm, self).save()
        self.instance.user.first_name = self.cleaned_data['first_name']
        self.instance.user.last_name = self.cleaned_data['last_name']
        self.instance.user.editor.country = self.cleaned_data['country']
        self.instance.user.editor.save()
        self.instance.user.save()
