# Generated by Django 4.2.15 on 2024-11-18 13:09

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0048_amendment_verb'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccentedTerms',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('terms', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024, verbose_name='terms'), blank=True, null=True, size=None)),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accented_terms', to='indigo_api.language', unique=True, verbose_name='language')),
            ],
            options={
                'verbose_name': 'accented terms',
                'verbose_name_plural': 'accented terms',
            },
        ),
    ]
