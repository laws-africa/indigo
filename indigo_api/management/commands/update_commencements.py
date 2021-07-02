import logging
from copy import copy

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import signals

from indigo.analysis.toc.base import CommencementsBeautifier
from indigo_api.models import Commencement, post_save_commencement


log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add all children of existing commenced provisions to provisions lists, as well as fully commenced parents.'
    provisions_added = None

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        if self.dry_run:
            log.info("Dry run, won't actually make changes.")

        # disable slack
        settings.SLACK_BOT_TOKEN = None
        # disconnect post-work save signal
        assert(signals.post_save.disconnect(post_save_commencement, sender=Commencement))

        with transaction.atomic():
            self.explode_provisions()
            if self.dry_run:
                log.info("Dry run!")
                raise Exception("Forcing rollback")

    def explode_provisions(self):
        # TODO: get commencements in order of oldest to newest,
        #  so that if e.g. Parts A and B in Chapter 1 fully commence on separate dates,
        #  Chapter 1 will be marked as commenced on the later date.
        for commencement in Commencement.objects.all():

            def add_descendants(p, commenced_list):
                for c in p.children:
                    if c.id not in commenced_list:
                        commencement.provisions.append(c.id)
                        self.provisions_added.append(c.id)
                    add_descendants(c, commenced_list)

            def check_existing_add_descendants(p, commenced_list):
                if p.basic_unit and p.id in commenced_list:
                    # this will recurse to the end of the tree, so no need to keep checking children
                    add_descendants(p, commenced_list)
                else:
                    # e.g. Chapter 1 wasn't on the list, but maybe section 1 was, so keep checking
                    for c in p.children:
                        check_existing_add_descendants(c, commenced_list)

            def add_containers(p):
                for c in p.children:
                    add_containers(c)

                if p.container and not p.commenced and (all(c.commenced for c in p.children)):
                    # this container is uncommenced but all its children are commenced; fix that
                    commencement.provisions.append(p.id)
                    self.provisions_added.append(p.id)
                    # update decoration
                    p.commenced = True

            def flattened_provisions(provisions):
                flattened = []

                def unpack(p):
                    flattened.append(p.id)
                    for c in p.children:
                        unpack(c)

                for p in provisions:
                    unpack(p)

                return flattened

            # TODO: link to edit.laws.africa for live run
            link = f"http://127.0.0.1:8000/works{commencement.commenced_work.frbr_uri}/commencements/#commencement-{commencement.pk}"

            # TODO: explicitly add all provisions individually for 'all provisions' commencements?
            if commencement.provisions:
                # Note: if subprovisions were added later,
                # they won't be added here because provisions will only get provisions up to this date
                provisions = commencement.commenced_work.all_commenceable_provisions(commencement.date)
                old_provisions_list = copy(commencement.provisions)
                self.provisions_added = []
                # first, add all descendants of existing provisions
                # e.g. sec_1 --> sec_1, sec_1__subsec_1, sec_1__subsec_2, etc.
                for prov in provisions:
                    check_existing_add_descendants(prov, old_provisions_list)
                # then, add fully commenced containers
                # e.g. sec_1, sec_2, sec_3 --> sec_1, …, part_a
                beautifier = CommencementsBeautifier(commenced=True)
                beautifier.decorate_provisions(provisions, commencement.provisions)
                for prov in provisions:
                    add_containers(prov)

                flattened = flattened_provisions(provisions)

                if self.provisions_added:
                    commencement.save()
                    log.info(f"Updated {link}:\n"
                             f"Added {self.provisions_added}\n\n"
                             f"to {old_provisions_list}\n\n"
                             f"Full new list: {commencement.provisions}\n\n"
                             f"Full possible list: {flattened}\n\n\n\n")
                else:
                    log.info(f"Encountered but didn't update {link}:\n"
                             f"Unchanged list: {commencement.provisions}.\n\n"
                             f"Full list: {flattened}\n\n\n\n")
            elif commencement.all_provisions:
                log.info(f"Encountered but didn't update {link}:\n"
                         f"All provisions were marked as commenced, nothing to worry about.\n\n")
            else:
                log.info(f"Encountered but didn't update {link}:\n"
                         f"All provisions were NOT marked as commenced, but there were no provisions to update.\n")
