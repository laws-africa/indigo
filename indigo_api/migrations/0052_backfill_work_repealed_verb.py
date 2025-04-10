# Generated by Django 4.2.15 on 2025-04-03 18:06

from django.db import migrations


def backfill_work_repealed_verb(apps, schema_editor):
    """ Update existing repealed works to have 'repealed' as their repealed_verb.
    """
    Work = apps.get_model('indigo_api', 'Work')
    db_alias = schema_editor.connection.alias

    for work in Work.objects.using(db_alias).filter(repealed_date__isnull=False).only('repealed_verb').iterator(300):
        work.repealed_verb = 'repealed'
        work.save(update_fields=['repealed_verb'])


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0051_work_repealed_note_work_repealed_verb'),
    ]

    operations = [
        migrations.RunPython(backfill_work_repealed_verb, migrations.RunPython.noop, elidable=True)
    ]
