from lxml import etree

from indigo.xmlutils import unwrap_element


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

        for hcontainer in xml.xpath('//a:hcontainer[@name="crossheading"]', namespaces={'a': ns}):
            changed = True

            # change to crossHeading
            hcontainer.tag = '{%s}crossHeading' % ns
            del hcontainer.attrib['name']

            # unwrap heading text
            heading = hcontainer.find('a:heading', {'a': ns})
            unwrap_element(heading)

            # TODO: re-write eIds, for both the changed element and siblings

        return changed
