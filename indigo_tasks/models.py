# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from indigo_api.models import Country, Locality, Work, Document
from django.contrib.auth.models import User

import datetime


class Task(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False, default='New task: %s' % (datetime.date.today()))
    content = models.TextField(null=True, blank=True)

    country = models.ForeignKey(Country, related_name='tasks', null=False, blank=False, on_delete=models.CASCADE)
    locality = models.ForeignKey(Locality, related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)
    work = models.ForeignKey(Work, related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)

    # cf indigo_api.models.Annotation
    anchor_id = models.CharField(max_length=128, null=True, blank=True)

    state = models.CharField(max_length=128, null=True, blank=True, choices=(
        ('open', 'open'), ('cancelled', 'cancelled'), ('pending', 'pending review'), ('closed', 'done')
    ), default='open')

    assignee = models.ForeignKey(User, related_name='tasks_assigned', null=True, blank=True, on_delete=models.SET_NULL)

    created_by = models.ForeignKey(User, related_name='tasks_authored', null=True, on_delete=models.SET_NULL)
    updated_by = models.ForeignKey(User, related_name='+', null=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def place_code(self):
        return self.country.code + '-' + self.locality.code if self.locality else self.country.code


class Workflow(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False, default='New workflow: %s' % (datetime.date.today()))
    description = models.TextField(null=True, blank=True)

    tasks = models.ManyToManyField(Task, related_name='workflows', null=True, blank=True)

    # people should add as many columns as works for that workflow; we'll start them off with these two by default
    columns = ['to do', 'done']

    # 'done' tasks / total tasks for workflow as a blunt measure of completeness
    completeness = models.IntegerField()


class TaskDiscussionItem(models.Model):
    task = models.ForeignKey(Task, related_name='discussion_items', null=False)
    content = models.TextField()


class WorkflowDiscussionItem(models.Model):
    workflow = models.ForeignKey(Workflow, related_name='discussion_items', null=False)
    content = models.TextField()


class Label(models.Model):
    label_text = models.CharField(max_length=128, null=False, blank=False)
    task = models.ForeignKey(Task, related_name='labels', null=True, on_delete=models.SET_NULL)
