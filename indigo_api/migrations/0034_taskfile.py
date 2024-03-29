# Generated by Django 3.2.13 on 2024-02-27 11:52

from django.db import migrations, models
import django.db.models.deletion
import indigo_api.models.tasks


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0033_workalias'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, null=True, upload_to=indigo_api.models.tasks.task_file_filename)),
                ('url', models.URLField(blank=True, null=True)),
                ('size', models.IntegerField(null=True)),
                ('filename', models.CharField(max_length=1024)),
                ('mime_type', models.CharField(max_length=1024)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='input_file',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_as_input', to='indigo_api.taskfile'),
        ),
        migrations.AddField(
            model_name='task',
            name='output_file',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_as_output', to='indigo_api.taskfile'),
        ),
    ]
