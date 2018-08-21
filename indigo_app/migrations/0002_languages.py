# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.OneToOneField(to='languages_plus.Language', on_delete=models.CASCADE)),
            ],
            options={'ordering': ['language__name_en']},
            bases=(models.Model,),
        ),
    ]
