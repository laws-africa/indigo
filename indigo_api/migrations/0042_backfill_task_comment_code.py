# Generated by Django 4.2.15 on 2024-08-28 06:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0041_citationalias'),
    ]

    operations = [
        migrations.RunSQL(
            """
UPDATE indigo_api_task
SET code = 'comment'
WHERE id IN (
    SELECT task_id
    FROM indigo_api_annotation
)
            """
        ),
    ]
