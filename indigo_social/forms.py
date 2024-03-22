import sys
from io import BytesIO

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import _lazy_re_compile, RegexValidator
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from PIL import Image

from indigo_api.models import Country, User
from indigo_social.models import UserProfile
from indigo_social.badges import badges
from pinax.badges.models import BadgeAward


class UserProfileForm(forms.ModelForm):
    validate_username = RegexValidator(
        _lazy_re_compile(r'^[-a-z0-9_]+\Z'),
        _("Your username cannot include spaces, punctuation or capital letters."),
        'invalid'
    )

    first_name = forms.CharField(label=_('First name'))
    last_name = forms.CharField(label=_('Last name'))
    username = forms.CharField(label=_('Username'), validators=[validate_username])
    country = forms.ModelChoiceField(required=True, queryset=Country.objects, label=_('Country'), empty_label=None)
    new_profile_photo = forms.ImageField(label=_('Profile photo'), required=False)
    language = forms.ChoiceField(label=_('Language'), choices=settings.LANGUAGES)

    class Meta:
        model = UserProfile
        fields = (
            # personal info (also includes first_name and last_name)
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
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError(_("This username is already taken."))
        return username

    def save(self, commit=True):
        if self.cleaned_data.get('new_profile_photo'):
            self.instance.profile_photo = process_profile_photo(self.cleaned_data['new_profile_photo'])
            self.instance.generate_nonce()

        if '_delete_photo' in self.data:
            self.instance.profile_photo.delete(save=False)

        super(UserProfileForm, self).save()

        self.instance.user.first_name = self.cleaned_data['first_name']
        self.instance.user.last_name = self.cleaned_data['last_name']
        self.instance.user.username = self.cleaned_data['username']
        self.instance.user.editor.country = self.cleaned_data['country']
        self.instance.user.editor.language = self.cleaned_data['language']
        self.instance.user.editor.save()
        self.instance.user.save()


def badge_choices():
    return sorted([(b.slug, '%s – %s' % (b.name, b.description)) for b in badges.registry.values() if b.can_award_manually])


def process_profile_photo(profile_photo):
    """ Process uploaded profile photo to meet specifications as follows:
    - crop into a square if image is not
    - resize to 200*200
    - convert to jpeg
    """
    uploaded_photo = Image.open(profile_photo)
    file_name = profile_photo.name.split('.')[0]
    output = BytesIO()
    width, height = uploaded_photo.size

    if width != height:
        new_width = min(width, height)

        left = (width - new_width)/2
        top = (height - new_width)/2
        right = (width + new_width)/2
        bottom = (height + new_width)/2
        uploaded_photo = uploaded_photo.crop((left, top, right, bottom))
    
    uploaded_photo = uploaded_photo.resize((200, 200), Image.ANTIALIAS)
    if not uploaded_photo.mode == 'RGB':
        uploaded_photo = uploaded_photo.convert('RGB')

    uploaded_photo.save(output, format='jpeg', quality=100)
    output.seek(0)
    resized_profile_photo = InMemoryUploadedFile(output, 'ImageField', '{}.jpeg'.format(file_name),
                                                 'image/jpeg', sys.getsizeof(output), None)
    return resized_profile_photo


class AwardBadgeForm(forms.Form):
    badge = forms.ChoiceField(choices=badge_choices)
    next = forms.CharField(required=False)

    def __init__(self, user=None, *args, **kwargs):
        super(AwardBadgeForm, self).__init__(*args, **kwargs)
        if user:
            self.setup_badges(user)

    def setup_badges(self, user):
        # filter possible badges to only those that the user doesn't already have
        awarded = [b.slug for b in BadgeAward.objects.filter(user=user)]
        self.fields['badge'].choices = [b for b in self.fields['badge'].choices if b[0] not in awarded]

    def actual_badge(self):
        return badges.registry.get(self.cleaned_data.get('badge'))


class UnawardBadgeForm(AwardBadgeForm):
    def setup_badges(self, user):
        # filter possible badges to only those that the user already has
        awarded = [b.slug for b in BadgeAward.objects.filter(user=user)]
        self.fields['badge'].choices = [b for b in self.fields['badge'].choices if b[0] in awarded]
