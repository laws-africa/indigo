import re
from collections import Counter

from indigo.xmlutils import rewrite_ids


class AKNMigration(object):
    def migrate_document(self, document):
        return self.migrate_act(document.doc, mappings={})

    def safe_update(self, element, mappings, old, new):
        """ Updates ids and mappings:
        - First, check `mappings` for `old`:
            if it's already there, check that it maps to `new`.
        - Then, update `mappings` and rewrite_ids (if it's already in mappings it'll get overwritten).
        """
        if old in mappings:
            assert mappings[old] == new, f'new id mapping {old} to {new} differs from existing {mappings[old]}'
        mappings.update(rewrite_ids(element, old, new))

    def traverse_mappings(self, mappings, old):
        if old in mappings:
            old = self.traverse_mappings(mappings, mappings[old])

        return old


class ScheduleArticleToHcontainer(AKNMigration):
    """ Change from using article as the main schedule container
    to using hcontainer.

    Migrates:

        <mainBody>
          <article id="schedule2">
            <heading>BY-LAWS REPEALED BY SECTION 99</heading>
            <paragraph id="schedule2.paragraph-0">

    to:

        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subeading>BY-LAWS REPEALED BY SECTION 99</subeading>
            <paragraph id="schedule2.paragraph-0">
    """
    def migrate_act(self, act):
        changed = False

        for article in act.root.xpath('//a:mainBody/a:article', namespaces={'a': act.namespace}):
            changed = True

            # change to hcontainer
            article.tag = '{%s}hcontainer' % act.namespace
            article.set('name', 'schedule')

            # make heading a subheading
            try:
                heading = article.heading
                heading.tag = '{%s}subheading' % act.namespace
            except AttributeError:
                pass

            # add a new heading
            alias = article.getparent().getparent().meta.identification.FRBRWork.FRBRalias.get('value')
            heading = act.maker.heading(alias)
            article.insert(0, heading)

        return changed


class FixSignificantWhitespace(AKNMigration):
    """ Strip unnecessary whitespace from p, heading, subheading and listIntroduction
    elements.

    In the past, we pretty-printed our XML which introduced meaningful whitespace. This
    migration removes it.
    """
    def migrate_document(self, document):
        xml = self.strip_whitespace(document.document_xml)
        if xml != document.document_xml:
            document.reset_xml(xml, from_model=True)
            return True

    def strip_whitespace(self, xml):
        opening = re.compile(r'<(p|heading|subheading|listIntroduction)>\n\s+<')
        xml = opening.sub('<\\1><', xml)

        closing = re.compile(r'\s*\n\s+</(p|heading|subheading|listIntroduction)>')
        xml = closing.sub('</\\1>', xml)

        return xml


class UpdateAKNNamespace(AKNMigration):
    """ Update all instances of:
    <akomaNtoso xmlns="http://www.akomantoso.org/2.0" xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    to
    <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
    """
    def update_namespace(self, xml):
        xml = xml.replace(
            ' xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd"',
            "",
            1)\
            .replace(
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            "",
            1)\
            .replace(
            'xmlns="http://www.akomantoso.org/2.0"',
            'xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"',
            1)

        return xml


class CrossheadingToHcontainer(AKNMigration):
    """ Updates crossheading ids to hcontainer and numbers them from 1, e.g.
        <hcontainer id="schedule2.crossheading-0" name="crossheading"> ->
        <hcontainer id="schedule2.hcontainer_1" name="crossheading">
    """
    def migrate_act(self, act, mappings):
        for crossheading in act.root.xpath('//a:hcontainer[@name="crossheading"]', namespaces={"a": act.namespace}):
            # new id is based on the number of preceding hcontainer siblings
            num = len(crossheading.xpath("preceding-sibling::a:hcontainer", namespaces={"a": act.namespace})) + 1
            old_id = crossheading.get("id")
            new_id = re.sub("crossheading-(\d+)$", f"hcontainer_{num}", old_id)
            self.safe_update(crossheading, mappings, old_id, new_id)


class UnnumberedParagraphsToHcontainer(AKNMigration):
    """ Update all instances un-numbered paragraphs to hcontainers. Slaw generates these when
    a block of text is encountered in a hierarchical element.

    This ALSO changes the id of the element to match AKN 3 styles, but using the id attribute (not eId)

    <paragraph id="section-1.paragraph0">
      <content>
        <p>text</p>
      </content>
    </paragraph>

    becomes

    <hcontainer id="section-1.hcontainer_1">
      <content>
        <p>text</p>
      </content>
    </hcontainer>
    """
    def migrate_act(self, act, mappings):
        for para in act.root.xpath('//a:paragraph[not(a:num)]', namespaces={'a': act.namespace}):
            para.tag = f'{{{act.namespace}}}hcontainer'
            # new id is based on the number of preceding hcontainer siblings
            num = len(para.xpath('preceding-sibling::a:hcontainer', namespaces={'a': act.namespace})) + 1
            old_id = para.get('id')
            new_id = re.sub('paragraph(\d+)$', f'hcontainer_{num}', old_id)
            self.safe_update(para, mappings, old_id, new_id)


class ComponentSchedulesToAttachments(AKNMigration):
    """ Migrates schedules stored as components to attachments, as a child of the act.

    This also moves the heading and subheading out of the hcontainer
    and into the attachment.

    This ALSO changes the id of the element to match AKN 3 styles, but using the id attribute (not eId)

    <akomaNtoso>
      <act>...</act>
      ...
      <components>
        <component id="component-schedule2">
          <doc name="schedule2">
            <meta>
              ...
            <mainBody>
              <hcontainer id="schedule2" name="schedule">
                <heading>Schedule 2</heading>
                <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
                <paragraph id="schedule2.paragraph0">
                  <content>
                    ...

    becomes

    <akomaNtoso>
      <act>
        ...
        <attachments>
          <attachment id="att_1">
            <heading>Schedule 2</heading>
            <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
            <doc name="schedule">
              <meta>
                ...
              <mainBody>
                <paragraph id="schedule2.paragraph0">
                  <content>
                    ...
    """

    def migrate_act(self, act, mappings):
        nsmap = {'a': act.namespace}

        for elem in act.root.xpath('/a:akomaNtoso/a:components', namespaces=nsmap):
            elem.tag = f'{{{act.namespace}}}attachments'
            # move to last child of act element
            act.main.append(elem)

            for i, att in enumerate(elem.xpath('a:component[a:doc]', namespaces=nsmap)):
                att.tag = f'{{{act.namespace}}}attachment'
                old_id = att.get('id')
                new_id = f'att_{i + 1}'
                self.safe_update(att, mappings, old_id, new_id)

                # heading and subheading
                for heading in att.doc.mainBody.hcontainer.xpath('a:heading | a:subheading', namespaces=nsmap):
                    att.doc.addprevious(heading)

                att.doc.set('name', 'schedule')

                # rewrite ids
                hcontainer = att.doc.mainBody.hcontainer
                id = hcontainer.get('id') + "."
                for child in hcontainer.iterchildren():
                    hcontainer.addprevious(child)
                    self.safe_update(child, mappings, id, '')

                # remove hcontainer
                att.doc.mainBody.remove(hcontainer)


class AKNeId(AKNMigration):
    """ In a document's XML, translate existing `id` attributes to `eId`
    and follow the new naming and numbering convention
    e.g. "sec_2" instead of "section-2"
    """
    basic_replacements = {
        # TODO: make sure all have been added
        # TODO: add a test for each type
        "chapter": (r"\bchapter-", "chp_"),
        "part": (r"\bpart-", "part_"),
        "subpart": (r"\bsubpart-", "subpart_"),
        "section": (r"\bsection-", "sec_"),
        "paragraph": (r"\bparagraph-", "para_"),
        "article": (r"\barticle-", "article_"),
    }

    add_1_replacements = {
        "table": (re.compile(r"\btable(?P<num>\d+)$"), "table_"),
        "blockList": (re.compile(r"\blist(?P<num>\d+)$"), "list_"),
    }

    complex_replacements = {
        # e.g. sec_3a.2A.4.1 --> sec_3a.subsec_2A-4-1
        "subsection": (re.compile(r"^[^.]+(?P<num>(\.\d[\dA-Za-z]*)+)$"), "subsec_"),
        # e.g. sec_3a.subsec_2-4-1.list_0.b --> sec_3a.subsec_2-4-1.list_0.item_b
        # or sec_3a.subsec_2-4-1.list_0.3.1 --> sec_3a.subsec_2-4-1.list_0.item_3-1
        # or sec_4.subsec_4.list_0.item_c.list_0.i --> sec_4.subsec_4.list_0.item_c.list_0.item_i
        "item": (re.compile(r"^([^.]+\.)+list_\d+(?P<num>(\.[\da-zA-Z]+)+)$"), "item_"),
    }

    def migrate_act(self, doc, mappings):
        """ Update the xml,
            - first by updating the values of `id` attributes as necessary,
            - and then by replacing all `id`s with `eId`s
        """
        nsmap = {"a": doc.namespace}

        # basic replacements, e.g. "chapter-" to "chap_"
        for element, (pattern, replacement) in self.basic_replacements.items():
            for node in doc.root.xpath(f"//a:{element}", namespaces=nsmap):
                old_id = node.get("id")
                new_id = re.sub(pattern, replacement, old_id)
                self.safe_update(node, mappings, old_id, new_id)

        # add one to n (previously 0-indexed)
        for element, (pattern, replacement) in self.add_1_replacements.items():
            for node in doc.root.xpath(f"//a:{element}", namespaces=nsmap):
                old_id = node.get("id")
                num = str(int(pattern.search(old_id).group("num")) + 1)
                new_id = re.sub(pattern, replacement + num, old_id)
                self.safe_update(node, mappings, old_id, new_id)

        # more complex replacements
        for element, (pattern, replacement) in self.complex_replacements.items():
            for node in doc.root.xpath(f"//a:{element}", namespaces=nsmap):
                old_id = node.get("id")
                # note: this assumes that all subsections and items have <num>s, which _should_ be true
                num = node.num.text
                num = self.clean_number(num)
                prefix = self.get_parent_id(node)
                new_id = f"{prefix}.{replacement}{num}"
                self.safe_update(node, mappings, old_id, new_id)

        # generate correct term ids, based on the parent id
        counter = Counter()
        for node in doc.root.xpath('//a:term', namespaces=nsmap):
            old_id = node.get('id')
            prefix = self.get_parent_id(node)
            # the num for this term depends on the number of preceding terms with the same prefix
            counter[prefix] += 1
            new_id = f'{prefix}__term_{counter[prefix]}'
            self.safe_update(node, mappings, old_id, new_id)

        # finally
        # "." separators
        for node in doc.root.xpath("//a:*[@id]", namespaces=nsmap):
            old_id = node.get("id")
            if "." in old_id:
                new_id = old_id.replace(".", "__")
                node.set("id", new_id)
                mappings.update({old_id: new_id})

        # replace all `id`s with `eId`s
        for node in doc.root.xpath("//a:*[@id]", namespaces=nsmap):
            node.set("eId", node.get("id"))
            del node.attrib["id"]

    def clean_number(self, num):
        # e.g. 1.3.2. / (3) / (dA) / (12 bis)
        return num.strip("().").replace(" ", "").replace(".", "-")

    def get_parent_id(self, node):
        parent = node.getparent()
        parent_id = parent.get("id")
        return parent_id if parent_id else self.get_parent_id(parent)


class HrefMigration(AKNMigration):
    """ Update all internal cross-references in a document's XML.
        Note: this will only update references if they still existed in the document at the time of running the previous migrations.
        If the section referred to was removed from the document for some reason in the interim, its id won't have been updated and the href therefore won't be in `mappings`.
        The reference would point at nothing in any case, but the nothing it points to would be an old-style id.
    """
    def migrate_act(self, doc, mappings):
        for node in doc.root.xpath("//a:ref[starts-with(@href, '#')]", namespaces={"a": doc.namespace}):
            ref = node.get("href").lstrip("#")
            new_ref = self.traverse_mappings(mappings, ref)
            node.set("href", f"#{new_ref}")


class AnnotationsMigration(AKNMigration):
    """ Update all the annotation anchors on a Document
    """
    def migrate_act(self, doc, mappings):
        for annotation in doc.annotations.all():
            annotation.anchor_id = self.traverse_mappings(mappings, annotation.anchor_id)
            annotation.save()
