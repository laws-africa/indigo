# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import string
import datetime

from django.db import migrations

from cobalt.act import Act, FrbrUri


def random_frbr_uri(country=None):
    today = datetime.datetime.now()
    number = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in xrange(5))
    country = country or 'za'
    return FrbrUri(country=country.lower(), locality=None, doctype="act",
                   subtype=None, actor=None, date=str(today.year),
                   expression_date=today.strftime("%Y-%m-%d"),
                   number=number.lower())


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
