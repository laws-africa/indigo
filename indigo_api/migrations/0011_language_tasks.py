# Generated by Django 2.2.24 on 2021-12-02 12:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0010_migrate_crossheadings'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='language',
            options={'base_manager_name': 'objects', 'ordering': ['language__name_en']},
        ),
        migrations.AlterModelOptions(
            name='task',
            options={'permissions': (('submit_task', 'Can submit an open task for review'), ('cancel_task', 'Can cancel a task that is open or has been submitted for review'), ('reopen_task', 'Can reopen a task that is closed or cancelled'), ('unsubmit_task', 'Can unsubmit a task that has been submitted for review'), ('close_task', 'Can close a task that has been submitted for review'), ('close_any_task', 'Can close any task that has been submitted for review, regardless of who submitted it'), ('block_task', 'Can block a task from being done, and unblock it'), ('exceed_task_limits', 'Can be assigned tasks in excess of limits'))},
        ),
    ]
