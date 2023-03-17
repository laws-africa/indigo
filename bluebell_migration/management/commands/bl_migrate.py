from django.conf import settings
from django.urls import reverse

from indigo_api.models import User
from bluebell_migration.management.commands.bb_migrate import Command as SlawToBluebellCommand
from bluebell_migration.migrate import pretty_c14n, DefsParaToBlocklist, DoNotMigrate


class Command(SlawToBluebellCommand):
    help = 'Migrate one or more bluebell documents or works to have blocklists, not hierarchical elements, ' \
           'in the definitions section.'
    migration_class = DefsParaToBlocklist
    doc_url = 'bl_migrate_document'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--user-id', type=str,
                            help='User ID for reversions'
                            )
        parser.add_argument('--skip-list', type=str,
                            help='List of Work FRBR URIs that should NOT be migrated semicolon-separated, e.g. '
                                 '/akn/za/act/1962/58;/akn/za-cpt/act/by-law/2020/beekeeping'
                            )

    def setup(self, options):
        super().setup(options)
        self.user = User.objects.get(pk=options['user_id'])
        skip_list = options.get('skip_list') or ''
        self.skip_list = skip_list.split(';')
        self.manually_update = []

    def finish_up(self):
        # don't write eid mappings to stdout
        self.stdout.write(f'Manually update these (skipped during migration): {self.manually_update}')

    def migrate_doc(self, doc):
        # check FRBR URI against skip list
        if doc.work.frbr_uri in self.skip_list:
            self.manually_update.append(doc.pk)
            raise DoNotMigrate(msg=f'  Skipping because in skip list: {doc}')

        old_xml = doc.document_xml
        try:
            self.migration.migrate_document(doc)
        except DoNotMigrate as e:
            self.manually_update.append(doc.pk)
            raise e

        # save eid mappings
        self.eidMappings[doc.id] = dict(self.migration.eid_mappings)

        is_valid, errors = self.migration.validate(pretty_c14n(doc.document_xml))
        url = settings.INDIGO_URL + reverse(self.doc_url, kwargs={'frbr_uri': doc.frbr_uri, 'doc_id': doc.id})

        # stability check
        if self.check:
            if self.migration.stability_diff(doc):
                # just a warning is fine in some cases
                self.stderr.write(self.style.WARNING(f'  Migrated document is not stable: {doc} -- check {url} for details'))

            if self.migration.content_fingerprint_diff(old_xml, doc.document_xml):
                # don't just warn, skip it instead
                self.manually_update.append(doc.pk)
                raise DoNotMigrate(msg=f'  Migrated document has different content to the original: {doc} -- check {url} for details')

            if not is_valid:
                # don't just warn, skip it instead
                self.manually_update.append(doc.pk)
                raise DoNotMigrate(msg=f'  Migrated document does not validate: {errors}; {doc} -- check {url} for details')

        if self.commit:
            # make new version rather than updating document_xml
            doc.save_with_revision(self.user, comment='Definitions paragraphs to blocklists (items)')
            self.stderr.write(
                self.style.SUCCESS(f'  Successfully migrated {doc}'))

            # rewrite annotation eids
            count = self.migration.migrate_annotations(doc)
            if count:
                self.stderr.write(self.style.NOTICE(f'  Updated {count} annotations'))

        # never migrate versions
        if self.migrate_versions:
            pass
