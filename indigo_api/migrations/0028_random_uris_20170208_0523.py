# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from indigo_api.models import random_frbr_uri
from cobalt.act import Act


def randomise_uris(apps, schema_editor):
    # randomise the FRBR URIs that are the old-style generic "/za/act/1980/01" URIs.
    Document = apps.get_model("indigo_api", "Document")
    for doc in Document.objects.filter(frbr_uri='/za/act/1980/01'):
        uri = random_frbr_uri()
        uri.date = str(doc.created_at.year)

        act = Act(doc.document_xml)
        act.frbr_uri = uri.work_uri(False)
        doc.frbr_uri = uri.work_uri(False)
        doc.document_xml = act.to_xml()
        doc.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0027_auto_20160220_2005'),
    ]

    operations = [
        migrations.RunPython(randomise_uris, noop)
    ]
