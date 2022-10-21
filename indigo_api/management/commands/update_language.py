import logging
from copy import copy

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from indigo.analysis.toc.base import CommencementsBeautifier, descend_toc_pre_order
from indigo_api.models import Commencement, Document

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """ See https://github.com/laws-africa/indigo/issues/1586 for details
    """
    help = 'Correct three-letter language codes from ISO-639-2B to ISO-639-2T. This is only necessary for documents' \
           ' with one of these legacy language codes: tib cze wel ger gre baq per fre arm ice geo mao mac may bur dut rum slo alb chi.' \
           ' See https://github.com/laws-africa/indigo/issues/1586 for details'

    codes = 'tib cze wel ger gre baq per fre arm ice geo mao mac may bur dut rum slo alb chi'.split()

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        if self.dry_run:
            log.info("Dry run, won't actually make changes.")

        with transaction.atomic():
            self.update_languages()
            if self.dry_run:
                log.info("Dry run!")
                raise Exception("Forcing rollback")

    def update_languages(self):
        for doc in Document.objects.filter(language__language__iso_639_2B__in=self.codes).iterator(10):
            log.info(f"Updating {doc} -- {doc.expression_frbr_uri}")
            doc.save()
