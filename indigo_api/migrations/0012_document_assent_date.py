# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0011_auto_20150505_1356'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='assent_date',
            field=models.DateField(help_text=b'Date signed by the president', null=True, blank=True),
            preserve_default=True,
        ),
    ]
