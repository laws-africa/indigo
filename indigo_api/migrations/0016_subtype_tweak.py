# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0015_auto_20150520_1455'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subtype',
            name='abbreviation',
            field=models.CharField(help_text=b'Short abbreviation to use in FRBR URI. No punctuation.', unique=True, max_length=20),
            preserve_default=True,
        ),
    ]
