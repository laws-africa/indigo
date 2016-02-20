# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0026_colophon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='colophon',
            name='body',
            field=models.TextField(),
            preserve_default=True,
        ),
    ]
