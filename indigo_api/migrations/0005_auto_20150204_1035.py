# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0004_auto_20150204_0948'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='publication_date',
            field=models.DateField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='publication_name',
            field=models.CharField(help_text=b'Name of the original publication, such as a national gazette.', max_length=1024, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='publication_number',
            field=models.CharField(help_text=b"Publication's sequence number, such as a gazette number.", max_length=1024, null=True),
            preserve_default=True,
        ),
    ]
