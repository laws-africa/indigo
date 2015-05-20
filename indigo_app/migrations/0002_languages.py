# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from indigo_app.models import Language, MasterLanguage


def forwards(apps, schema_editor):
    Language(language=MasterLanguage.objects.get(iso_639_2B='afr')).save()
    Language(language=MasterLanguage.objects.get(iso_639_2B='eng')).save()
    Language(language=MasterLanguage.objects.get(iso_639_2B='fre')).save()
    Language(language=MasterLanguage.objects.get(iso_639_2B='por')).save()
    Language(language=MasterLanguage.objects.get(iso_639_2B='swa')).save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.OneToOneField(to='languages_plus.Language')),
            ],
            options={'ordering': ['language__name_en']},
            bases=(models.Model,),
        ),
        migrations.RunPython(forwards, backwards),
    ]
