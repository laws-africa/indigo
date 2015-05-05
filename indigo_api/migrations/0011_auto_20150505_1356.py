# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0010_auto_20150505_1315'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='publication_date',
        ),
        migrations.RemoveField(
            model_name='document',
            name='publication_name',
        ),
        migrations.RemoveField(
            model_name='document',
            name='publication_number',
        ),
    ]
