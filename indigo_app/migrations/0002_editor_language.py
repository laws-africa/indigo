# Generated by Django 3.2.15 on 2023-04-25 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_app', '0001_squashed_0021'),
    ]

    operations = [
        migrations.AddField(
            model_name='editor',
            name='language',
            field=models.CharField(default='en-us', help_text='Preferred language', max_length=10),
        ),
    ]