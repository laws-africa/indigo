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
        # only get commencements that have provisions
        # (they're already ordered by date ascending)
        commencements = Commencement.objects.select_for_update().exclude(provisions=[])
        n_total = commencements.count()
        ix = 0
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

                if p.container and not p.commenced and all(c.commenced for c in p.children) \
                        and any(c.id in commencement.provisions for c in p.children):
                    # this container is uncommenced but all its children are commenced,
                    # and at least one commenced at the present commencement's date
                    commencement.provisions.append(p.id)
                    # update decoration
                    p.commenced = True

                elif p.container and not p.commenced and any(c.id in commencement.provisions for c in p.children):
                    log.info(f"\n\nContainer NOT marked as commenced: {p.title} ({p.id}).\n"
                             f"Double-check that this container should not have commenced on this date, "
                             f"or fix manually later.\n"
                             f"Commenced children: {[c.id for c in p.children if c.commenced]}\n"
                             f"Uncommenced children: {[c.id for c in p.children if not c.commenced]}\n\n")

            ix += 1
            log.info(f"\nUpdating {settings.INDIGO_URL}/works{commencement.commenced_work.frbr_uri}/commencements/#commencement-{commencement.pk} ({ix} of {n_total}):")
            # Note: if subprovisions were added later,
            # they won't be added here because `provisions` will only get provisions up to this commencement's date
            provisions = commencement.commenced_work.all_commenceable_provisions(commencement.date)
            old_provisions_list = copy(commencement.provisions)

            # first, add all descendants of existing provisions
            # e.g. sec_1 --> sec_1, sec_1__subsec_1, sec_1__subsec_2, etc.
            check_existing_add_descendants(provisions, commencement.provisions)

            # then, add fully commenced containers
            # if different parts of a container commenced on different dates,
            # it'll be marked as commenced on the first date that any of its children commenced
            # e.g. sec_1, sec_2, sec_3 --> sec_1, …, part_a
            beautifier = CommencementsBeautifier()
            # all commencements on this work, excluding this commencement
            almost_all_commencements = commencements\
                .filter(commenced_work=commencement.commenced_work)\
                .exclude(pk=commencement.pk)
            # add in this commencement's provisions separately, because it hasn't been saved yet
            all_commenced_ids = [p_id for c in almost_all_commencements for p_id in c.provisions] \
                + commencement.provisions
            provisions = beautifier.decorate_provisions(provisions, all_commenced_ids)
            for prov in provisions:
                add_containers(prov)

            # fresh commencement.provisions in the right order
            commencement.provisions = [p.id for p in descend_toc_pre_order(provisions)
                                       if p.id in commencement.provisions]

            # alert about partially commenced basic units, only on final commencement per commenced work
            if not commencements.filter(commenced_work=commencement.commenced_work, date__gt=commencement.date):
                all_provisions = commencement.commenced_work.all_commenceable_provisions()
                updated_commenced_ids = [p_id for c in almost_all_commencements
                                         for p_id in c.provisions] + commencement.provisions
                all_provisions = beautifier.decorate_provisions(all_provisions, updated_commenced_ids)
                basic_units_flagged = [
                    p.id for p in descend_toc_pre_order(all_provisions)
                    if p.commenced and p.basic_unit and p.children and not p.all_descendants_same]
                if basic_units_flagged:
                    log.info(f"\n\nBasic units NOT fully commenced:\n"
                             f"{', '.join(basic_units_flagged)}.\n"
                             f"Explicitly add a commencement for each subprovision – "
                             f"usually its date of insertion.\n\n")

            if any(pid for pid in commencement.provisions if pid not in old_provisions_list):
                commencement.save()
                log.info("\nUPDATE DONE!")
            else:
                log.info("\nNO UPDATE:")

            log.info(f"\nOld list: {old_provisions_list}\n\n"
                     f"New list: {commencement.provisions}\n\n\n")
