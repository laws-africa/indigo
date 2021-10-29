import re
from lxml import etree

from indigo.xmlutils import unwrap_element, rewrite_ids


class RealCrossHeadings:
    """ Migrate old-style hcontainer cross-heading to crossHeading
    """
    def migrate_document(self, document):
        root = etree.fromstring(document.content)
        if self.migrate_xml(root, document.doc.namespace):
            document.content = etree.tostring(root, encoding='unicode')
            return True

    def migrate_xml(self, xml, ns):
        changed = False
        parents = set()
        self.eidMappings = {}

        for hcontainer in xml.xpath('//a:hcontainer[@name="crossheading"]', namespaces={'a': ns}):
            changed = True
            parents.add(hcontainer.getparent())

            # change to crossHeading
            hcontainer.tag = '{%s}crossHeading' % ns
            del hcontainer.attrib['name']

            # unwrap heading text
            heading = hcontainer.find('a:heading', {'a': ns})
            unwrap_element(heading)

        # re-write eIds, for both the changed elements and any conflicting siblings
        for parent in parents:
            # rewrite new crossHeadings
            for i, crossHeading in enumerate(parent.xpath('./a:crossHeading', namespaces={'a': ns})):
                old_id = crossHeading.get('eId')
                new_id = re.sub(r'hcontainer_\d+$', f'crossHeading_{i + 1}', old_id)
                self.eidMappings.update(rewrite_ids(crossHeading, old_id, new_id))

            # now re-write all hcontainers
            for i, hcontainer in enumerate(parent.xpath('./a:hcontainer', namespaces={'a': ns})):
                old_id = hcontainer.get('eId')
                new_id = re.sub(r'hcontainer_\d+$', f'hcontainer_{i + 1}', old_id)
                self.eidMappings.update(rewrite_ids(hcontainer, old_id, new_id))

        return changed
