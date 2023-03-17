from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from lxml import etree

from indigo_app.views.works import WorkViewBase

from bluebell_migration.migrate import SlawToBluebell, DefsParaToBlocklist, diff_table, pretty_c14n
from bluebell.parser import AkomaNtosoParser


class WorkViewBluebellMigration(WorkViewBase, DetailView):
    template_name_suffix = '_bb_migration'
    migration = SlawToBluebell

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        migration = self.migration()
        context['docs'] = self.work.document_set.no_xml().all()
        for doc in context['docs']:
            doc.must_migrate = migration.should_migrate(doc)
        context['must_migrate'] = any(d.must_migrate for d in context['docs'])

        return context


class DocumentViewBluebellMigration(WorkViewBase, DetailView):
    template_name_suffix = '_bb_migration_doc'
    migration = SlawToBluebell

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = self.work.document_set.no_xml()
        context['doc'] = doc = get_object_or_404(qs, pk=self.kwargs['doc_id'])

        migration = self.migration()
        context['must_migrate'] = migration.should_migrate(doc)

        if context['must_migrate']:
            old_content = doc.content
            migration.migrate_document(doc)

            # main xml diff
            old_xml = pretty_c14n(old_content)
            migrated_xml = pretty_c14n(doc.content)
            context['xml_diff'] = diff_table(old_xml, migrated_xml, fromdesc="Original XML", todesc="Migrated XML")

            # original unparsed vs migrated unparsed
            parser = AkomaNtosoParser(doc.frbr_uri)
            original_unparsed = parser.unparse(etree.fromstring(old_content))
            migrated_unparsed = parser.unparse(etree.fromstring(doc.content))
            context['unparsed_diff'] = diff_table(original_unparsed, migrated_unparsed, "Original unparsed",
                                                  "Migrated unparsed")

            # stability check
            context['stability_diff'] = migration.stability_diff(doc)
            context['stability_passed'] = bool(not(context['stability_diff']))

            # content fingerprint
            context['content_fingerprint_diff'] = migration.content_fingerprint_diff(old_content, doc.content)
            context['content_fingerprint_passed'] = bool(not(context['content_fingerprint_diff']))

            # validate
            context['validates'], context['validation_errors'] = migration.validate(pretty_c14n(doc.content))

            # quality check
            # start with the original, then unparse original as bluebell, re-parse as bluebell, and compare resulting xml
            doc.reset_xml(old_content, from_model=True)
            migration.reparse_as_bluebell(doc)
            reparsed_xml = pretty_c14n(doc.content)
            context['quality_diff'] = diff_table(migrated_xml, reparsed_xml, "Migrated XML", "Re-parsed original")

        return context


class DocumentViewBluebellMigrationBl(DocumentViewBluebellMigration):
    template_name_suffix = '_bl_migration_doc'
    migration = DefsParaToBlocklist
