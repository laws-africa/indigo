# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_app', '0005_delete_subtype'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='country',
            options={'ordering': ['country__name'], 'verbose_name_plural': 'Countries'},
        ),
    ]
