import logging
from copy import copy

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from indigo.analysis.toc.base import CommencementsBeautifier, descend_toc_pre_order
from indigo_api.models import Commencement


log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add all children of existing commenced provisions to provisions lists, as well as fully commenced parents.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        if self.dry_run:
            log.info("Dry run, won't actually make changes.")

        with transaction.atomic():
            self.explode_provisions()
            if self.dry_run:
                log.info("Dry run!")
                raise Exception("Forcing rollback")

    def explode_provisions(self):
        commencements = Commencement.objects.all()
        for commencement in commencements:

            def check_existing_add_descendants(provs, commenced_list):
                # don't use descend_toc_pre_order() because it'll duplicate effort
                for p in provs:
                    if p.id in commenced_list:
                        # this will recurse to the end of the tree, so no need to keep checking children
                        commencement.provisions.extend([c.id for c in descend_toc_pre_order(p.children)
                                                        if c.id not in commenced_list])
                    else:
                        # e.g. Chapter 1 wasn't on the list, but maybe section 1 was, so keep checking
                        check_existing_add_descendants(p.children, commenced_list)

            def add_containers(p):
                # don't use descend_toc_post_order() because the decoration doesn't update
                for c in p.children:
                    add_containers(c)

                if p.container and not p.commenced and (all(c.commenced for c in p.children)):
                    # this container is uncommenced but all its children are commenced; fix that
                    commencement.provisions.append(p.id)
                    # update decoration
                    p.commenced = True

            link = f"{settings.INDIGO_URL}/works{commencement.commenced_work.frbr_uri}/commencements/#commencement-{commencement.pk}"

            if commencement.provisions:
                # Note: if subprovisions were added later,
                # they won't be added here because `provisions` will only get provisions up to this commencement's date
                provisions = commencement.commenced_work.all_commenceable_provisions(commencement.date)
                flattened = [p.id for p in descend_toc_pre_order(provisions)]
                old_provisions_list = copy(commencement.provisions)

                # first, add all descendants of existing provisions
                # e.g. sec_1 --> sec_1, sec_1__subsec_1, sec_1__subsec_2, etc.
                check_existing_add_descendants(provisions, commencement.provisions)

                # then, add fully commenced containers
                # if different parts of a container commenced on different dates,
                # it'll be marked as commenced on the latest date
                # e.g. sec_1, sec_2, sec_3 --> sec_1, …, part_a
                beautifier = CommencementsBeautifier()
                # all commencements on this work to this date, excluding this commencement
                commencements_to_present = commencements.filter(
                    commenced_work=commencement.commenced_work, date__lte=commencement.date,
                ).exclude(pk=commencement.pk)
                # add in this commencement's provisions separately, because it hasn't been saved yet
                commenced_ids_to_present = [p_id for c in commencements_to_present
                                            for p_id in c.provisions] + commencement.provisions
                beautifier.decorate_provisions(provisions, commenced_ids_to_present)
                for prov in provisions:
                    add_containers(prov)

                # fresh commencement.provisions in the right order
                commencement.provisions = [p.id for p in descend_toc_pre_order(provisions)
                                           if p.id in commencement.provisions]

                provisions_added = [pid for pid in commencement.provisions if pid not in old_provisions_list]

                if provisions_added:
                    commencement.save()
                    log.info(f"Updated {link}:\n"
                             f"Added {provisions_added}\n\n"
                             f"to {old_provisions_list}\n\n"
                             f"Full new list: {commencement.provisions}\n\n"
                             f"Full possible list: {flattened}\n\n\n\n")
                else:
                    log.info(f"Encountered but didn't update {link}:\n"
                             f"Unchanged list: {commencement.provisions}.\n\n"
                             f"Full list: {flattened}\n\n\n\n")
            elif not commencement.all_provisions:
                log.info(f"Encountered but didn't update {link}:\n"
                         f"All provisions were NOT marked as commenced, but there were no provisions to update.\n\n")
