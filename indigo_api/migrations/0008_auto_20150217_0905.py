# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0007_document_deleted'),
    ]

    operations = [
        migrations.RenameField(
            model_name='document',
            old_name='uri',
            new_name='frbr_uri',
        ),
    ]
