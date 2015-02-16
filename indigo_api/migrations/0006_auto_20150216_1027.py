# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0005_auto_20150204_1035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='publication_name',
            field=models.CharField(help_text=b'Name of the original publication, such as a national gazette', max_length=1024, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='publication_number',
            field=models.CharField(help_text=b"Publication's sequence number, such as a gazette number", max_length=1024, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='uri',
            field=models.CharField(help_text=b'Used globably to identify this document', max_length=512),
            preserve_default=True,
        ),
    ]
