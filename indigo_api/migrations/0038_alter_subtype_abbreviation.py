# Generated by Django 3.2.13 on 2024-03-22 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0037_taxonomytopic_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subtype',
            name='abbreviation',
            field=models.CharField(help_text='Short abbreviation to use in the FRBR URI. No punctuation.', max_length=32, unique=True, verbose_name='abbreviation'),
        ),
    ]
