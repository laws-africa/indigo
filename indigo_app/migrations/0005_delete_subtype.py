# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_app', '0004_country'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Subtype',
        ),
    ]
