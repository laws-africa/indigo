# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import arrow
from django.db import models, migrations
from indigo_api.models import Document


def forwards(apps, schema_editor):
    for doc in Document.objects.only('document_xml', 'expression_date').all():
        doc.expression_date = doc.publication_date or arrow.now().date()
        doc.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0020_subtype'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='expression_date',
            field=models.DateField(help_text=b'Date of publication or latest amendment', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(forwards, backwards),
    ]
