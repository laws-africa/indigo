# coding=utf-8
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from reversion.models import Version
from reversion import revisions as reversion

from indigo_api.models import Work, post_save_work


class Command(BaseCommand):
    help = 'Ensure that all works have a revision.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def get_works(self, country):
        return Work.objects.filter(country=country, publication_document=None)

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        if self.dry_run:
            self.stdout.write(self.style.NOTICE('Dry-run, won\'t actually make changes'))

        # disable slack
        settings.SLACK_BOT_TOKEN = None
        # disconnect post-work save signal
        assert(signals.post_save.disconnect(post_save_work, sender=Work))

        with transaction.atomic():
            self.create_revisions()
            if self.dry_run:
                raise Exception("Forcing rollback")

    def create_revisions(self):
        # works that are missing revisions
        ct = ContentType.objects.get_for_model(Work)

        query = Work.objects.exclude(id__in=Version.objects.filter(content_type=ct.pk).values_list('object_id_int', flat=True))
        date = None

        def on_revision_commit(**kwargs):
            # update the revision with the date of the last update
            kwargs['revision'].date_created = date
            kwargs['revision'].save()
        reversion.post_revision_commit.connect(on_revision_commit)

        for work in query:
            user = work.updated_by_user or work.created_by_user
            if user:
                work.updated_by_user = work.updated_by_user or user
                with reversion.create_revision():
                    reversion.set_user(user)
                    date = work.updated_at or work.created_at
                    work.save()

                self.stdout.write(self.style.SUCCESS("Created revision for {}".format(work)))

            else:
                self.stdout.write(self.style.NOTICE("Work {} doesn't have a user".format(work)))
