# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('countries_plus', '0002_auto_20150120_2225'),
        ('indigo_api', '0025_auto_20150921_1025'),
    ]

    operations = [
        migrations.CreateModel(
            name='Colophon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Name of this colophon', max_length=1024)),
                ('body', tinymce.models.HTMLField()),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='countries_plus.Country', help_text=b'Which country does this colophon apply to?', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
