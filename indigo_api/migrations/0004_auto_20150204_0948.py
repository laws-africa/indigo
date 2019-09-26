# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0003_auto_20150114_1549'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='publication_name',
            field=models.CharField(max_length=1024, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='publication_number',
            field=models.CharField(help_text=b'eg. Gazette number', max_length=1024, null=True),
            preserve_default=True,
        ),
    ]
