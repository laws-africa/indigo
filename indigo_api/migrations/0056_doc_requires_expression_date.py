# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-07-30 19:42
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0055_document_expression_dates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='expression_date',
            field=models.DateField(help_text=b'Date of publication or latest amendment'),
        ),
    ]