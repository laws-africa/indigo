# Generated by Django 4.2.15 on 2024-09-27 11:11
import logging

from django.db import migrations

log = logging.getLogger(__name__)


def ensure_filename_unique(attachment):
    old_filename = attachment.filename
    # deal with the odd case of e.g. 'chap 200' as a filename, with no extension
    try:
        filename, extension = attachment.filename.rsplit('.', 1)
        extension = f'.{extension}'
    except ValueError:
        log.error(f'Missing extension: {old_filename}')
        filename = attachment.filename
        extension = ''
    other_attachment_filenames = attachment.document.attachments.only('filename')\
        .exclude(pk=attachment.pk).values_list('filename', flat=True)
    add_num = 0
    while attachment.filename in other_attachment_filenames:
        add_num += 1
        attachment.filename = f'{filename}-{add_num}{extension}'

    # did it change?
    return old_filename != attachment.filename, old_filename


def attachment_filenames_unique(apps, schema_editor):
    Attachment = apps.get_model("indigo_api", "Attachment")
    db_alias = schema_editor.connection.alias
    for attachment in Attachment.objects.using(db_alias).only('filename').iterator(1000):
        changed, old_filename = ensure_filename_unique(attachment)
        if changed:
            log.info(f'Old filename: {old_filename}')
            attachment.save(update_fields=['filename'])
            log.info(f'New filename: {attachment.filename}')


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0045_taxonomytopic_copy_from_principal'),
    ]

    operations = [
        migrations.RunPython(attachment_filenames_unique, migrations.RunPython.noop, elidable=True),
    ]