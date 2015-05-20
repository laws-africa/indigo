# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0018_delete_subtype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='country',
            field=models.CharField(default=b'za', max_length=2),
            preserve_default=True,
        ),
    ]
