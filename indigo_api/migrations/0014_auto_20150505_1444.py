# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('indigo_api', '0013_document_stub'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='tags',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='stub',
            field=models.BooleanField(default=False, help_text=b'This is a placeholder document without full content'),
            preserve_default=True,
        ),
    ]
