# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True, default='', help_text="A short bio")
    qualifications = models.TextField(blank=True, null=True, default='', help_text="Qualifications")
    skills = models.TextField(blank=True, null=True, default='', help_text="Skills")
    organisations = models.TextField(blank=True, null=True, default='', help_text="Organisation(s)")
    specialisations = models.TextField(blank=True, null=True, default='', help_text="Specialisation(s)")
    areas_of_law = models.CharField(max_length=256, blank=True, null=True, default='', help_text="Area(s) of law")
    profile_photo = models.ImageField(blank=True, null=True)
    twitter_username = models.CharField(max_length=256, blank=True, null=True, default='')
    linkedin_profile = models.URLField(blank=True, null=True, default='')


@receiver(post_save, sender=User)
def create_user_profile(sender, **kwargs):
    # create a user profile for each new user object
    user = kwargs["instance"]
    if not hasattr(user, "userprofile") and not kwargs.get("raw"):
        user_profile = UserProfile(user=user)
        user_profile.save()
