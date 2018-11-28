# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from indigo_api.models import Country, Locality, Work, Document


class Task(models.Model):
    title = models.CharField(max_length=256)
    content = models.TextField()

    country = models.ForeignKey(Country, related_name='tasks', null=False, blank=False, on_delete=models.CASCADE)
    locality = models.ForeignKey(Locality, related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)
    work = models.ForeignKey(Work, related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, related_name='tasks', null=True, blank=True)
    anchor = models.CharField(max_length=128, null=True, blank=True)

    # state
    closed = models.BooleanField(default=False, null=False)

    # do we need created_by_user, created_when, etc?

    @property
    def place_code(self):
        return self.country.code + '-' + self.locality.code if self.locality else self.country.code


class Workflow(models.Model):
    title = models.CharField(max_length=256)
    content = models.TextField()

    tasks = models.ManyToManyField(Task, related_name='workflows', null=True, blank=True)

    # we want people to be able to add as many columns as they like; each column should be a string
    # columns to do with review tasks might be special
    # (imagining dragging a task into the final column and that autogenerating a review task)
    columns = ['to do', 'ready for review']

    # tasks in final column / total tasks (should some tasks weigh more?)
    completeness = models.IntegerField()


class TaskDiscussionItem(models.Model):
    task = models.ForeignKey(Task, related_name='discussion_items', null=False, blank=False)
    content = models.TextField()


class WorkflowDiscussionItem(models.Model):
    workflow = models.ForeignKey(Workflow, related_name='discussion_items', null=False, blank=False)
    content = models.TextField()
