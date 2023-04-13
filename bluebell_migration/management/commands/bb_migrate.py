import json

from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import reverse
from django.db.transaction import atomic
from reversion.models import Version

from indigo_api.models import Work, Country, Commencement
from bluebell_migration.migrate import SlawToBluebell, pretty_c14n, DoNotMigrate


class Command(BaseCommand):
    help = 'Migrate one or more slaw-based documents or works to bluebell.'
    migration_class = SlawToBluebell
    doc_url = 'bb_migrate_document'

    def add_arguments(self, parser):
        parser.add_argument('--work', type=str,
                            help='Work FRBR URI to migrate'
                            )
        parser.add_argument('--place', type=str,
                            help='Place code to migrate'
                            )
        parser.add_argument('--commit', action='store_true', default=False,
                            help='Commit changes to the database.'
                            )
        parser.add_argument('--no-checks', action='store_true', default=False,
                            help='Don\'t perform checks.'
                            )
        parser.add_argument('--no-versions', action='store_true', default=False,
                            help='Don\'t migrate document versions.'
                            )
        parser.add_argument('--skip-list', type=str,
                            help='List of Work FRBR URIs that should NOT be migrated, semicolon-separated, e.g. '
                                 '/akn/za/act/1962/58;/akn/za-cpt/act/by-law/2020/beekeeping'
                            )

    def setup(self, options):
        self.commit = options['commit']
        self.check = not(options['no_checks'])
        self.migrate_versions = not options['no_versions']
        self.eidMappings = {}
        skip_list = options.get('skip_list') or ''
        self.skip_list = skip_list.split(';')
        self.manually_update = []

    def finish_up(self):
        self.stderr.write(f'Manually update these (skipped during migration): {self.manually_update}')
        # write eid mappings to stdout (everything else goes to stderr)
        self.stdout.write(json.dumps(self.eidMappings))

    def handle(self, *args, **options):
        self.setup(options)

        if self.commit:
            self.stderr.write(self.style.WARNING('WILL commit changes to the db'))
        else:
            self.stderr.write(self.style.WARNING('Dry-run: WILL NOT commit changes to the db'))

        with atomic():
            if options['work']:
                work = Work.objects.get(frbr_uri=options['work'])
                self.migrate_work(work)

            elif options['place']:
                country, locality = Country.get_country_locality(options['place'])
                qs = Work.objects.filter(country=country, locality=locality).order_by('-pk')
                self.stderr.write(self.style.NOTICE(f'Migrating {qs.count()} works for {options["place"]}'))
                for work in qs.iterator(10):
                    self.migrate_work(work)

        self.finish_up()

    def migrate_work(self, work):
        # this includes deleted documents
        docs = work.document_set.order_by('-pk')
        if not docs.exists():
            return

        self.stderr.write(self.style.NOTICE(f'Migrating {len(docs)} documents for {work}'))

        work_mappings = {}
        for doc in docs.iterator(10):
            self.migration = self.migration_class()
            if not self.migration.should_migrate(doc):
                self.stderr.write(self.style.NOTICE(f'No need to migrate {doc}'))
                continue

            self.stderr.write(self.style.NOTICE(f'Migrating {doc}'))
            try:
                self.migrate_doc(doc)
            except DoNotMigrate as e:
                self.stderr.write(
                    self.style.WARNING(f'  Document not migrated: {doc}\n  Error message: {e.msg}'))
                continue
            work_mappings.update(self.eidMappings[doc.id])

        # to rewrite commencement provision eids, we need to merge together all the provision ids for all documents
        count = self.migrate_commencements(work, work_mappings)
        if count:
            self.stderr.write(self.style.NOTICE(f'  Updated {count} commencement provisions'))

    def migrate_doc(self, doc):
        # check FRBR URI against skip list
        if doc.work.frbr_uri in self.skip_list:
            self.manually_update.append(doc.pk)
            raise DoNotMigrate(msg=f'  Skipping because in skip list: {doc}')

        old_xml = doc.document_xml
        try:
            self.migration.migrate_document(doc)
        except DoNotMigrate:
            self.manually_update.append(doc.pk)
            raise

        # save eid mappings
        self.eidMappings[doc.id] = dict(self.migration.eid_mappings)

        is_valid, errors = self.migration.validate(pretty_c14n(doc.document_xml))
        url = settings.INDIGO_URL + reverse(self.doc_url, kwargs={'frbr_uri': doc.frbr_uri, 'doc_id': doc.id})

        # stability check
        if self.check:
            if self.migration.stability_diff(doc):
                self.stderr.write(self.style.WARNING(f'  Migrated document is not stable: {doc} -- check {url} for details'))

            if self.migration.content_fingerprint_diff(old_xml, doc.document_xml):
                self.stderr.write(self.style.WARNING(f'  Migrated document has different content to the original: {doc} -- check {url} for details'))

            if not is_valid:
                self.stderr.write(self.style.WARNING(f'  Migrated document does not validate: {errors}; {doc} -- check {url} for details'))

        if self.commit:
            doc.save(update_fields=['document_xml'])

            # rewrite annotation eids
            count = self.migration.migrate_annotations(doc)
            if count:
                self.stderr.write(self.style.NOTICE(f'  Updated {count} annotations'))

        if self.migrate_versions:
            self.stderr.write(self.style.NOTICE(f'  Migrating historical versions'))

            for version in Version.objects.get_for_object(doc).order_by('-pk').iterator():
                self.stderr.write(self.style.NOTICE(f'    Migrating version {version.pk}'))

                # this loads the XML directly from the json representation, migrates it, and puts it back into
                # the version object, which must then save if it has changed
                if self.migration.migrate_document_version(version):
                    if self.commit:
                        version.save(update_fields=['serialized_data'])

    def migrate_commencements(self, work, mappings):
        total = 0

        for commencement in Commencement.objects.filter(commenced_work_id=work.id, all_provisions=False):
            count = 0

            for i, old_id in enumerate(commencement.provisions):
                new_id = mappings.get(old_id, old_id)
                if old_id != new_id:
                    count += 1
                    commencement.provisions[i] = new_id

            if count:
                commencement.save()

            total += count

        return total
