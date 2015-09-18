# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import indigo_api.models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0023_auto_20150614_1338'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='document',
            options={'permissions': (('publish_document', 'Can publish and edit non-draft documents'),)},
        ),
        migrations.AlterField(
            model_name='attachment',
            name='file',
            field=models.FileField(upload_to=indigo_api.models.attachment_filename),
            preserve_default=True,
        ),
    ]
