# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0016_subtype_tweak'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='language',
            field=models.CharField(default=b'eng', max_length=3),
            preserve_default=True,
        ),
    ]
