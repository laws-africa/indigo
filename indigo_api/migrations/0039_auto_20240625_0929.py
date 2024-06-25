# Generated by Django 3.2.18 on 2024-06-25 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0038_alter_subtype_abbreviation'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='vocabularytopic',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='vocabularytopic',
            name='vocabulary',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='country',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='created_by_user',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='locality',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='tasks',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='updated_by_user',
        ),
        migrations.RemoveField(
            model_name='work',
            name='taxonomies',
        ),
        migrations.AlterField(
            model_name='document',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, help_text='Timestamp of when the expression was first created.', verbose_name='created at'),
        ),
        migrations.AlterField(
            model_name='document',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, help_text='Timestamp of when the expression was last updated.', verbose_name='updated at'),
        ),
        migrations.AlterField(
            model_name='taxonomytopic',
            name='description',
            field=models.TextField(blank=True, help_text='Description of the topic', null=True, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='taxonomytopic',
            name='name',
            field=models.CharField(help_text='Name of the taxonomy topic', max_length=512, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='taxonomytopic',
            name='slug',
            field=models.SlugField(help_text='Unique short name (code) for the topic.', max_length=4096, unique=True, verbose_name='slug'),
        ),
        migrations.DeleteModel(
            name='TaxonomyVocabulary',
        ),
        migrations.DeleteModel(
            name='VocabularyTopic',
        ),
        migrations.DeleteModel(
            name='Workflow',
        ),
    ]