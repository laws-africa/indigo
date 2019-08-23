# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_app', '0002_languages'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subtype',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Name of the document subtype', max_length=1024)),
                ('abbreviation', models.CharField(help_text=b'Short abbreviation to use in FRBR URI. No punctuation.', unique=True, max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
