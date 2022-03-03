import re
import json
from django.utils.encoding import force_text
from lxml import etree

from indigo.xmlutils import unwrap_element, rewrite_ids


class DataMigration:
    def migrate_document_version(self, version):
        data = json.loads(force_text(version.serialized_data.encode("utf8")))[0]
        fields = data['fields']
        if fields.get('document_xml'):
            xml = etree.fromstring(fields['document_xml'])
            changed, xml = self.migrate_xml(xml)
            if changed:
                fields['document_xml'] = etree.tostring(xml, encoding='unicode')
                version.serialized_data = json.dumps([data])
                return True

    def migrate_document_xml(self, document):
        """ Migrate the raw document XML. This is useful in migrations where
        we don't have access to the full document model's support methods.
        """
        xml = etree.fromstring(document.document_xml)
        self.ns = xml.nsmap[None]
        changed, xml = self.migrate_xml(xml)
        if changed:
            document.document_xml = etree.tostring(xml, encoding='unicode')
        return changed

    def migrate_xml(self, xml):
        """ Migrates an XML document, returning tuple (changed, xml) where
        changed is a boolean indicating if the document has changed, and xml
        is the migrated XML document.
        """
        raise NotImplemented()


class RealCrossHeadings(DataMigration):
    """ Migrate old-style hcontainer cross-heading to crossHeading
    """
    def migrate_document(self, document):
        self.ns = document.doc.namespace
        root = etree.fromstring(document.content)
        changed, root = self.migrate_xml(root)
        if changed:
            document.content = etree.tostring(root, encoding='unicode')
            return True

    def migrate_xml(self, xml):
        changed = False
        parents = set()
        self.eid_mappings = {}

        for hcontainer in xml.xpath('//a:hcontainer[@name="crossheading"]', namespaces={'a': self.ns}):
            changed = True
            parents.add(hcontainer.getparent())
            self.migrate_element(hcontainer)

        # re-write eIds, for both the changed elements and any conflicting siblings
        for parent in parents:
            # rewrite new crossHeadings
            for i, crossHeading in enumerate(parent.xpath('./a:crossHeading', namespaces={'a': self.ns})):
                old_id = crossHeading.get('eId')
                if old_id:
                    new_id = re.sub(r'hcontainer_\d+$', f'crossHeading_{i + 1}', old_id)
                    self.eid_mappings.update(rewrite_ids(crossHeading, old_id, new_id))

            # now re-write all hcontainers
            for i, hcontainer in enumerate(parent.xpath('./a:hcontainer', namespaces={'a': self.ns})):
                old_id = hcontainer.get('eId')
                if old_id:
                    new_id = re.sub(r'hcontainer_\d+$', f'hcontainer_{i + 1}', old_id)
                    self.eid_mappings.update(rewrite_ids(hcontainer, old_id, new_id))

        return changed, xml

    def migrate_element(self, hcontainer):
        # change to crossHeading
        hcontainer.tag = '{%s}crossHeading' % self.ns
        del hcontainer.attrib['name']

        # unwrap heading text
        heading = hcontainer.find('a:heading', {'a': self.ns})
        unwrap_element(heading)


class CorrectAttachmentEids(DataMigration):
    """ Ensure that attachment eIds are correctly prefixed
    """
    def migrate_document(self, document):
        self.ns = document.doc.namespace
        changed, _ = self.migrate_xml(document.doc.root)
        return changed

    def migrate_xml(self, xml):
        changed = False
        self.eid_mappings = {}

        for att in xml.xpath('//a:attachment', namespaces={'a': self.ns}):
            changed = self.migrate_element(att) or changed

        return changed, xml

    def migrate_element(self, att):
        att_id = att.get('eId')
        changed = False

        for elem in att.xpath(f'.//a:*[@eId and not(starts-with(@eId, "{att_id}__"))]', namespaces={'a': self.ns}):
            changed = True
            new_id = f'{att_id}__{elem.attrib["eId"]}'
            self.eid_mappings[elem.attrib['eId']] = elem.attrib['eId'] = new_id

        return changed
