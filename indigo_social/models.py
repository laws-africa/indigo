# -*- coding: utf-8 -*-
import os
from io import BytesIO
import sys

from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from PIL import Image

from urllib.request import urlretrieve, urlcleanup

from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialLogin, SocialAccount
from allauth.socialaccount.signals import pre_social_login, social_account_added, social_account_updated


def user_profile_photo_path(instance, filename):
    file_name, file_extension = os.path.splitext(filename)
    return 'avatars/{}'.format(instance.id)


def retrieve_social_profile_photo(user_profile, url):
    """ Retrieve and save a retrieved user's profile photo from a url
    """
    try:
        filename, _ = urlretrieve(url)
        user_profile.profile_photo.save(filename, File(open(filename, 'rb')))
    finally:
        urlcleanup()


def resize_photo(profile_photo, user):
    """ Resize and crop an uploaded profile photo to meet specifications
    """
    uploaded_profile_photo = Image.open(profile_photo)
    file_extension = profile_photo.name.split('.')[1]
    file_name = user.pk
    output = BytesIO()

    # TODO: crop then resize
    # profile_photo = uploaded_profile_photo.crop((0, 0, 200, 200))
    profile_photo = uploaded_profile_photo.resize((200, 200), Image.ANTIALIAS)
    profile_photo.save(output, format=file_extension, quality=100)
    output.seek(0)

    profile_photo = InMemoryUploadedFile(output, 
                                         'ImageField', 
                                         "{}.{}".format(file_name, file_extension),
                                         'image/{}'.format(file_extension), 
                                          sys.getsizeof(output),
                                          None)

    return profile_photo


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True, default='', help_text="A short bio")
    qualifications = models.TextField(blank=True, null=True, default='', help_text="Qualifications")
    skills = models.TextField(blank=True, null=True, default='', help_text="Skills")
    organisations = models.TextField(blank=True, null=True, default='', help_text="Organisation(s)")
    specialisations = models.TextField(blank=True, null=True, default='', help_text="Specialisation(s)")
    areas_of_law = models.CharField(max_length=256, blank=True, null=True, default='', help_text="Area(s) of law")
    profile_photo = models.ImageField(upload_to=user_profile_photo_path, blank=True, null=True)
    profile_photo_nonce = models.CharField(max_length=256, blank=True, null=True)
    twitter_username = models.CharField(max_length=256, blank=True, null=True, default='')
    linkedin_profile = models.URLField(blank=True, null=True, default='')

    def save(self):
        # TODO: Generate and save the nonce here
        self.profile_photo = resize_photo(self.profile_photo, self.user)

        super(UserProfile, self).save()

    @property
    def profile_photo_url(self):
        if not self.profile_photo:
            return "/static/images/avatars/default_avatar.svg"
        return reverse('indigo_social:user_profile_photo', kwargs={'username': self.user.username, 'nonce': '123'})
    

@receiver(post_save, sender=User)
def create_user_profile(sender, **kwargs):
    # create a user profile for each new user object
    user = kwargs["instance"]
    if not hasattr(user, "userprofile") and not kwargs.get("raw"):
        user_profile = UserProfile(user=user)
        user_profile.save()


@receiver(user_signed_up, sender=User)
def retrieve_profile_photo_on_signup(sender, **kwargs):
    user = kwargs['user']

    try:
        user_profile = UserProfile.objects.get(user=user)
        user_social_account = SocialAccount.objects.get(user=user, provider='google')
        url = user_social_account.extra_data.get('picture')
        retrieve_social_profile_photo(user_profile, url)

    except (SocialAccount.DoesNotExist, UserProfile.DoesNotExist):
        pass
