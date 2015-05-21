# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards(apps, schema_editor):
    from indigo_api.models import Subtype
    Subtype(name='By-law', abbreviation='by-law').save()
    Subtype(name='Statutory Instrument', abbreviation='si').save()
    Subtype(name='Government Notice', abbreviation='gn').save()
    Subtype(name='Proclamation', abbreviation='p').save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0019_tweak_country'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subtype',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Name of the document subtype', max_length=1024)),
                ('abbreviation', models.CharField(help_text=b'Short abbreviation to use in FRBR URI. No punctuation.', unique=True, max_length=20)),
            ],
            options={'verbose_name': 'Document subtype'},
            bases=(models.Model,),
        ),
        migrations.RunPython(forwards, backwards),
    ]
