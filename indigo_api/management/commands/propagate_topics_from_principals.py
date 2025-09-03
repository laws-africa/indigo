import logging
from copy import copy

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from indigo.analysis.toc.base import CommencementsBeautifier, descend_toc_pre_order
from indigo_api.models import Commencement, Document, TaxonomyTopic

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ensures that works with topics with the propagate_from_principal flag set, have those topics applied to all their related works.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        if self.dry_run:
            log.info("Dry run, won't actually make changes.")

        with transaction.atomic():
            self.propagate()
            if self.dry_run:
                log.info("Dry run!")
                raise Exception("Forcing rollback")

    def propagate(self):
        for topic in TaxonomyTopic.objects.filter(copy_from_principal=True).iterator(10):
            topic.propagate_copy_from_principal(works=None, add=True)
