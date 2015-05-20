# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from indigo_app.models import Country, MasterCountry


def forwards(apps, schema_editor):
    Country(country=MasterCountry.objects.get(iso='ZA')).save()
    Country(country=MasterCountry.objects.get(iso='ZM')).save()
    Country(country=MasterCountry.objects.get(iso='NA')).save()


def backwards(apps, schema_editor):
    pass


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
                ('country', models.OneToOneField(to='countries_plus.Country')),
            ],
            options={
                'ordering': ['country__name'],
            },
            bases=(models.Model,),
        ),
        migrations.RunPython(forwards, backwards),
    ]
