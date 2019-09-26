# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0017_tweak_language_field'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Subtype',
        ),
    ]
