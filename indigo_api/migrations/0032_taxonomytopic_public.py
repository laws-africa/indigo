# Generated by Django 3.2.13 on 2024-02-20 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0031_task_timeline_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxonomytopic',
            name='public',
            field=models.BooleanField(default=True),
        ),
    ]
