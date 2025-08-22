import json
import re

from django.utils.encoding import force_str
from lxml import etree

from bluebell.xml import IdGenerator
from cobalt.akn import get_maker
from docpipe.xmlutils import unwrap_element
from indigo.xmlutils import rewrite_ids


class DataMigration:
    def migrate_document_version(self, version):
        data = json.loads(force_str(version.serialized_data.encode("utf8")))[0]
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
        root = etree.fromstring(document.content.encode('utf-8'))
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


class DefinitionsIntoBlockContainers(DataMigration):
    """ Wrap definitions in <p>s and <blockList>s in <blockContainer>s; move the refersTo attribute up too.
    Before:
      <act>
        …
        <p refersTo="#term-board" eId="chp_1__sec_1__p_2">
          “<def refersTo="#term-board" eId="chp_1__sec_1__p_2__def_1">board</def>”
          means the board of the
          <term refersTo="#term-Regulator" eId="chp_1__sec_1__p_2__term_1">Regulator</term>
          contemplated in section <ref href="#chp_2__sec_9" eId="chp_1__sec_1__p_2__ref_1">9</ref>;
        </p>
        <p refersTo="#term-board_appeals_committee" eId="chp_1__sec_1__p_3">
          “<def refersTo="#term-board_appeals_committee" eId="chp_1__sec_1__p_3__def_1">board appeals committee</def>” means …;
        </p>
        <blockList refersTo="#term-new_works" eId="chp_1__sec_1__list_1">
          <listIntroduction eId="chp_1__sec_1__list_1__intro_1">“<def refersTo="#term-new_works" eId="chp_1__sec_1__list_1__intro_1__def_1">new works</def>” means—</listIntroduction>
          <item eId="chp_1__sec_1__list_1__item_a">
            <num>(a)</num>
            <p eId="chp_1__sec_1__list_1__item_a__p_1">a new <term refersTo="#term-railway_operation" eId="chp_1__sec_1__list_1__item_a__p_1__term_1">railway operation</term>, including new train, <term refersTo="#term-network" eId="chp_1__sec_1__list_1__item_a__p_1__term_2">network</term> or <term refersTo="#term-station" eId="chp_1__sec_1__list_1__item_a__p_1__term_3">station</term> operations;</p>
          </item>
          <item eId="chp_1__sec_1__list_1__item_b">
            <num>(b)</num>
            <p eId="chp_1__sec_1__list_1__item_b__p_1">the introduction of new technology including <term refersTo="#term-rolling_stock" eId="chp_1__sec_1__list_1__item_b__p_1__term_1">rolling stock</term>, train authorisation systems, traction power supplies or components thereof; or</p>
          </item>
          <item eId="chp_1__sec_1__list_1__item_c">
            <num>(c)</num>
            <p eId="chp_1__sec_1__list_1__item_c__p_1">an extension to an existing operation that has the potential to substantively increase the risk profile of the <term refersTo="#term-operator" eId="chp_1__sec_1__list_1__item_c__p_1__term_1">operator</term>;</p>
          </item>
        </blockList>
        …
      </act>
    After:
      <act>
        …
        <blockContainer refersTo="#term-board" eId="chp_1__sec_1__blockContainer_2">
          <p eId="chp_1__sec_1__blockContainer_2__p_1">
            “<def refersTo="#term-board" eId="chp_1__sec_1__blockContainer_2__p_1__def_1">board</def>”
            means the board of the
            <term refersTo="#term-Regulator" eId="chp_1__sec_1__blockContainer_2__p_1__term_1">Regulator</term>
            contemplated in section <ref href="#chp_2__sec_9" eId="chp_1__sec_1__blockContainer_2__p_1__ref_1">9</ref>;
          </p>
        </blockContainer>
        <blockContainer refersTo="#term-board_appeals_committee" eId="chp_1__sec_1__blockContainer_3">
          <p eId="chp_1__sec_1__blockContainer_3__p_1">
            “<def refersTo="#term-board_appeals_committee" eId="chp_1__sec_1__blockContainer_3__p_1__def_1">board appeals committee</def>” means …;
          </p>
        </blockContainer>
        <blockContainer refersTo="#term-new_works" eId="chp_1__sec_1__blockContainer_4">
          <blockList eId="chp_1__sec_1__blockContainer_4__list_1">
            <listIntroduction eId="chp_1__sec_1__blockContainer_4__list_1__intro_1">“<def refersTo="#term-new_works" eId="chp_1__sec_1__blockContainer_4__list_1__intro_1__def_1">new works</def>” means—</listIntroduction>
            <item eId="chp_1__sec_1__blockContainer_4__list_1__item_a">
              <num>(a)</num>
              <p eId="chp_1__sec_1__blockContainer_4__list_1__item_a__p_1">a new <term refersTo="#term-railway_operation" eId="chp_1__sec_1__blockContainer_4__list_1__item_a__p_1__term_1">railway operation</term>, including new train, <term refersTo="#term-network" eId="chp_1__sec_1__blockContainer_4__list_1__item_a__p_1__term_2">network</term> or <term refersTo="#term-station" eId="chp_1__sec_1__blockContainer_4__list_1__item_a__p_1__term_3">station</term> operations;</p>
            </item>
            <item eId="chp_1__sec_1__blockContainer_4__list_1__item_b">
              <num>(b)</num>
              <p eId="chp_1__sec_1__blockContainer_4__list_1__item_b__p_1">the introduction of new technology including <term refersTo="#term-rolling_stock" eId="chp_1__sec_1__blockContainer_4__list_1__item_b__p_1__term_1">rolling stock</term>, train authorisation systems, traction power supplies or components thereof; or</p>
            </item>
            <item eId="chp_1__sec_1__blockContainer_4__list_1__item_c">
              <num>(c)</num>
              <p eId="chp_1__sec_1__blockContainer_4__list_1__item_c__p_1">an extension to an existing operation that has the potential to substantively increase the risk profile of the <term refersTo="#term-operator" eId="chp_1__sec_1__blockContainer_4__list_1__item_c__p_1__term_1">operator</term>;</p>
            </item>
          </blockList>
        </blockContainer>
        …
      </act>
    """
    ns = None
    maker = None
    id_generator = None

    def migrate_document(self, document):
        self.ns = document.doc.namespace
        self.maker = get_maker()
        self.id_generator = IdGenerator()
        xml = etree.fromstring(document.document_xml)
        changed, xml = self.migrate_xml(xml)
        if changed:
            document.content = etree.tostring(xml, encoding='unicode')
            return True

    def migrate_xml(self, xml):
        changed = False

        # check existing blockContainers for missing 'definition' class
        existing_defn_xpath = etree.XPath(
            '//a:blockContainer[@refersTo and starts-with(@refersTo, "#term-")]',
            namespaces={'a': self.ns})
        for definition in existing_defn_xpath(xml):
            self.add_missing_class(definition)

        # start with a <def> tag and look upwards until we find an ancestor with a matching refersTo term
        # (if a matching ancestor isn't found, nothing happens -- we just move on to the next <def>)
        defn_xpath = etree.XPath(
            '//a:def[@refersTo and starts-with(@refersTo, "#term-")]',
            namespaces={'a': self.ns})
        for definition in defn_xpath(xml):
            # e.g. #term-Department
            defined_term = definition.attrib['refersTo']
            for parent in definition.iterancestors():
                # don't double-wrap <blockContainer>s
                if parent.tag == f'{{{self.ns}}}blockContainer' and parent.attrib.get('refersTo', '') == defined_term:
                    break
                if parent.attrib.get('refersTo', '') == defined_term:
                    self.migrate_element(parent)
                    changed = True
                    break

        if changed:
            self.id_generator.rewrite_all_eids(xml)

        return changed, xml

    def add_missing_class(self, elem):
        elem_class = elem.attrib.get('class')
        elem_classes = elem_class.split(' ') if elem_class else []
        if 'definition' not in elem_classes:
            elem_classes.append('definition')
            elem_class = ' '.join(elem_classes)
            elem.set('class', elem_class)

    def migrate_element(self, elem):
        refers_to = elem.attrib.pop('refersTo')
        assert refers_to.startswith('#term-')
        block_container = self.maker('blockContainer', refersTo=refers_to)
        block_container.set('class', 'definition')
        elem.addprevious(block_container)
        block_container.append(elem)
