# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_app', '0007_editor'),
    ]

    operations = [
        migrations.CreateModel(
            name='Locality',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Local name of this locality', max_length=512)),
                ('code', models.CharField(help_text=b'Unique code of this locality (used in the FRBR URI)', max_length=100)),
                ('country', models.ForeignKey(to='indigo_app.Country')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Localities',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='locality',
            unique_together=set([('country', 'code')]),
        ),
    ]
