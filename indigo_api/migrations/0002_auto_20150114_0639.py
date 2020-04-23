# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='country',
            field=models.CharField(default=b'za', max_length=5, choices=[(b'za', b'South Africa'), (b'zm', b'Zambia')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='content_xml',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='draft',
            field=models.BooleanField(default=True, help_text=b"Drafts aren't available through the public API"),
            preserve_default=True,
        ),
    ]
