# Generated by Django 3.2.13 on 2024-02-22 13:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0032_taxonomytopic_public'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkAlias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.CharField(help_text='Alias e.g. Penal Code, etc', max_length=255)),
                ('work', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliases', to='indigo_api.work')),
            ],
            options={
                'ordering': ('alias',),
                'unique_together': {('alias', 'work')},
            },
        ),
    ]
