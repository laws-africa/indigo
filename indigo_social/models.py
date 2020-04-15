# -*- coding: utf-8 -*-
import os

from django.contrib.auth.models import User
from django.core.files import File
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from urllib.request import urlretrieve, urlcleanup

from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialLogin, SocialAccount
from allauth.socialaccount.signals import pre_social_login, social_account_added, social_account_updated


def user_profile_photo_path(instance, filename):
    return 'avatars/{}/{}'.format(instance.id, os.path.basename(filename))


def retrieve_social_profile_photo(user_profile, url):
    """ Retrieve and save a retrieved user's profile photo from a url
    """
    try:
        filename, _ = urlretrieve(url)
        user_profile.profile_photo.save(filename, File(open(filename, 'rb')))
    finally:
        urlcleanup()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True, default='', help_text="A short bio")
    qualifications = models.TextField(blank=True, null=True, default='', help_text="Qualifications")
    skills = models.TextField(blank=True, null=True, default='', help_text="Skills")
    organisations = models.TextField(blank=True, null=True, default='', help_text="Organisation(s)")
    specialisations = models.TextField(blank=True, null=True, default='', help_text="Specialisation(s)")
    areas_of_law = models.CharField(max_length=256, blank=True, null=True, default='', help_text="Area(s) of law")
    profile_photo = models.ImageField(upload_to=user_profile_photo_path, blank=True, null=True)
    twitter_username = models.CharField(max_length=256, blank=True, null=True, default='')
    linkedin_profile = models.URLField(blank=True, null=True, default='')

    @property
    def profile_photo_url(self):
        if not self.profile_photo:
            return "/static/images/avatars/default_avatar.svg"
        return self.profile_photo
    

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
    user_profile = UserProfile.objects.get(user=user)

    try:
        user_social_account = SocialAccount.objects.get(user=user, provider='google')
        url = user_social_account.extra_data.get('picture')
        retrieve_social_profile_photo(user_profile, url)

    except SocialAccount.DoesNotExist:
        pass
