# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from indigo_api.models import Subtype


def forwards(apps, schema_editor):
    Subtype(name='By-law', abbreviation='by-law').save()
    Subtype(name='Statutory Instrument', abbreviation='si').save()
    Subtype(name='Government Notice', abbreviation='gn').save()
    Subtype(name='Proclamation', abbreviation='p').save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0014_auto_20150505_1444'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subtype',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Name of the document subtype', max_length=1024)),
                ('abbreviation', models.CharField(help_text=b'Short abbreviation to use in FRBR URI. No punctuation.', max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='document',
            name='country',
            field=models.CharField(default=b'na', max_length=2, choices=[(b'na', b'Namibia'), (b'za', b'South Africa'), (b'zm', b'Zambia')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='frbr_uri',
            field=models.CharField(default=b'/', help_text=b'Used globally to identify this work', max_length=512),
            preserve_default=True,
        ),
        migrations.RunPython(forwards, backwards),
    ]
