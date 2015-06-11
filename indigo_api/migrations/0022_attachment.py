# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0021_document_expression_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to=b'')),
                ('size', models.IntegerField()),
                ('filename', models.CharField(help_text=b'Unique attachment filename', max_length=255, db_index=True)),
                ('mime_type', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document', models.ForeignKey(related_name='attachments', to='indigo_api.Document')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
