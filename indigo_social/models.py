# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=1024, blank=True, null=True, help_text="A short bio")
    qualifications = models.TextField(max_length=512, blank=True, null=True, help_text="Qualifications")
    skills = models.TextField(max_length=256, blank=True, null=True, help_text="Skills")
    organisations = models.TextField(max_length=256, blank=True, null=True, help_text="Organisation(s)")
    specialisations = models.TextField(max_length=256, blank=True, null=True, help_text="Specialisation(s)")
    areas_of_law = models.CharField(max_length=256, blank=True, null=True, help_text="Area(s) of law")
    profile_photo = models.ImageField(blank=True, null=True)
    twitter_profile = models.URLField(blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
