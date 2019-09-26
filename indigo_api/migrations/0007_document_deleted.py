# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0006_auto_20150216_1027'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='deleted',
            field=models.BooleanField(default=False, help_text=b'Has this document been deleted?'),
            preserve_default=True,
        ),
    ]
