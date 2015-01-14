# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_dms', '0002_auto_20150114_0639'),
    ]

    operations = [
        migrations.RenameField(
            model_name='document',
            old_name='content_xml',
            new_name='document_xml',
        ),
    ]
