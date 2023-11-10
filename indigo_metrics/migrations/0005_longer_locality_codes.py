# Generated by Django 3.2.13 on 2023-11-10 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_metrics', '0004_documenteditactivity_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailyplacemetrics',
            name='place_code',
            field=models.CharField(db_index=True, max_length=120),
        ),
        migrations.AlterField(
            model_name='dailyworkmetrics',
            name='locality',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='dailyworkmetrics',
            name='place_code',
            field=models.CharField(db_index=True, max_length=120),
        ),
    ]
