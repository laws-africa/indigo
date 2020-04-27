# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0008_auto_20150217_0905'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='language',
            field=models.CharField(default=b'eng', max_length=6, choices=[(b'eng', b'English')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='frbr_uri',
            field=models.CharField(default=b'/', help_text=b'Used globably to identify this document', max_length=512),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='publication_date',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.CharField(default=b'(untitled)', max_length=1024, null=True),
            preserve_default=True,
        ),
    ]
