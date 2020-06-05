# coding=utf-8
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from reversion import revisions as reversion

from indigo_api.models import Document
from indigo_api.data_migrations.legacy import ScheduleArticleToHcontainer


class Command(BaseCommand):
    help = 'Migrate schedules from articles to hcontainers'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        if self.dry_run:
            self.stdout.write(self.style.NOTICE('Dry-run, won\'t actually make changes'))

        # disable slack
        settings.SLACK_BOT_TOKEN = None

        with transaction.atomic():
            self.migrate_schedules()
            if self.dry_run:
                raise Exception("Forcing rollback")

    def migrate_schedules(self):
        # works that are missing revisions
        docs = Document.objects.filter(document_xml__contains='<article')
        user = User.objects.get(pk=1)
        migration = ScheduleArticleToHcontainer()

        for doc in docs:
            if migration.migrate_document(doc):
                doc.refresh_xml()
                doc.updated_by_user = user

                with reversion.create_revision():
                    reversion.set_user(user)
                    doc.save()

                self.stdout.write(self.style.SUCCESS("Migrated doc #{} - {}".format(doc.pk, doc.work)))
