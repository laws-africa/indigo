# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from indigo_api.models import Country, Locality, Work, Document


class Issue(models.Model):
    title = models.CharField(max_length=256)
    description = models.TextField()
    # is the discussion thread part of 'description'?

    country = models.ForeignKey(Country)
    locality = models.ForeignKey(Locality)
    place_code = country.code + '-' + locality.code if locality else country.code

    work = models.ForeignKey(Work)
    document = models.ForeignKey(Document)

    # this should be something else but I don't know what; for accessing section in document
    doc_location = models.CharField(max_length=64)


class Workflow(models.Model):
    title = models.CharField(max_length=256)
    description = models.TextField()
    # is the discussion thread part of 'description'?

    issues = models.ManyToManyField(Issue)

    # we want people to be able to add as many columns as they like; each column should be a string
    # columns to do with review tasks might be special
    # (imagining dragging an issue into the final column and that autogenerating a review task)
    columns = ['to do', 'ready for review']

    # issues in final column / total issues (should some issues weight more?)
    completeness = models.IntegerField()
