# Generated by Django 2.2.14 on 2020-07-08 11:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('countries_plus', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('indigo_api', '0001_initial'),
        ('taggit', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='document',
            name='updated_by_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='document',
            name='work',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='indigo_api.Work'),
        ),
        migrations.AddField(
            model_name='country',
            name='country',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='countries_plus.Country'),
        ),
        migrations.AddField(
            model_name='country',
            name='primary_language',
            field=models.ForeignKey(help_text='Primary language for this country', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='indigo_api.Language'),
        ),
        migrations.AddField(
            model_name='commencement',
            name='commenced_work',
            field=models.ForeignKey(help_text='Principal work being commenced', on_delete=django.db.models.deletion.CASCADE, related_name='commencements', to='indigo_api.Work'),
        ),
        migrations.AddField(
            model_name='commencement',
            name='commencing_work',
            field=models.ForeignKey(help_text='Work that provides the commencement date for the principal work', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='commencements_made', to='indigo_api.Work'),
        ),
        migrations.AddField(
            model_name='commencement',
            name='created_by_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='commencement',
            name='updated_by_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='colophon',
            name='country',
            field=models.ForeignKey(help_text='Which country does this colophon apply to?', on_delete=django.db.models.deletion.CASCADE, to='indigo_api.Country'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='indigo_api.Document'),
        ),
        migrations.AddField(
            model_name='arbitraryexpressiondate',
            name='created_by_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='arbitraryexpressiondate',
            name='updated_by_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='arbitraryexpressiondate',
            name='work',
            field=models.ForeignKey(help_text='Work', on_delete=django.db.models.deletion.CASCADE, related_name='arbitrary_expression_dates', to='indigo_api.Work'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='created_by_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='annotation',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='indigo_api.Document'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='in_reply_to',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='indigo_api.Annotation'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='task',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotation', to='indigo_api.Task'),
        ),
        migrations.AddField(
            model_name='amendment',
            name='amended_work',
            field=models.ForeignKey(help_text='Work amended.', on_delete=django.db.models.deletion.CASCADE, related_name='amendments', to='indigo_api.Work'),
        ),
        migrations.AddField(
            model_name='amendment',
            name='amending_work',
            field=models.ForeignKey(help_text='Work making the amendment.', on_delete=django.db.models.deletion.CASCADE, related_name='amendments_made', to='indigo_api.Work'),
        ),
        migrations.AddField(
            model_name='amendment',
            name='created_by_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='amendment',
            name='updated_by_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='vocabularytopic',
            unique_together={('level_1', 'level_2', 'vocabulary')},
        ),
        migrations.AlterUniqueTogether(
            name='locality',
            unique_together={('country', 'code')},
        ),
        migrations.AlterUniqueTogether(
            name='documentactivity',
            unique_together={('document', 'user', 'nonce')},
        ),
        migrations.AlterUniqueTogether(
            name='commencement',
            unique_together={('commenced_work', 'commencing_work', 'date')},
        ),
        migrations.AlterUniqueTogether(
            name='arbitraryexpressiondate',
            unique_together={('date', 'work')},
        ),
    ]
