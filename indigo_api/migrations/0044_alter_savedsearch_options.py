# Generated by Django 4.2.15 on 2024-09-10 14:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0043_savedsearch'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='savedsearch',
            options={'ordering': ['name'], 'verbose_name': 'saved search', 'verbose_name_plural': 'saved searches'},
        ),
    ]
