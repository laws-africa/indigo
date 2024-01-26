# Generated by Django 3.2.23 on 2024-01-26 05:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0030_backfill_work_in_progress'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkAliases',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.CharField(blank=True, help_text='Alias e.g. Penal Code, etc', max_length=255, null=True)),
                ('work', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='work_aliases', to='indigo_api.work')),
            ],
        ),
    ]