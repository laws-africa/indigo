# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('countries_plus', '0002_auto_20150120_2225'),
        ('indigo_app', '0003_subtype'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country', models.OneToOneField(to='countries_plus.Country', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['country__name'],
            },
            bases=(models.Model,),
        ),
    ]
