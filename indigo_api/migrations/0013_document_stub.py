# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0012_document_assent_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='stub',
            field=models.BooleanField(default=False, help_text=b'Is this a placeholder stub with full content?'),
            preserve_default=True,
        ),
    ]
