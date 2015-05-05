# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0009_auto_20150308_1645'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='commencement_date',
            field=models.DateField(help_text=b'Date of commencement unless otherwise specified', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='frbr_uri',
            field=models.CharField(default=b'/', help_text=b'Used globably to identify this work', max_length=512),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='language',
            field=models.CharField(default=b'eng', max_length=3, choices=[(b'afr', b'Afrikaans'), (b'eng', b'English'), (b'fre', b'French'), (b'por', b'Portuguese'), (b'swa', b'Swahili')]),
            preserve_default=True,
        ),
    ]
