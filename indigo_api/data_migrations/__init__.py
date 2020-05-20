import re

from cobalt import Act

from indigo.xmlutils import rewrite_ids


class AKNMigration(object):
    def migrate_document(self, document):
        return self.migrate_act(document.doc)


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


class UpdateAKNNamespace:
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
    def migrate_act(self, act):
        for para in act.root.xpath('//a:paragraph[not(a:num)]', namespaces={'a': act.namespace}):
            para.tag = f'{{{act.namespace}}}hcontainer'
            # new id is based on the number of preceding hcontainer siblings
            num = len(para.xpath('preceding-sibling::a:hcontainer', namespaces={'a': act.namespace})) + 1
            old_id = para.get('id')
            new_id = re.sub('paragraph(\d+)$', f'hcontainer_{num}', old_id)
            rewrite_ids(para, old_id, new_id)


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

    def migrate_act(self, act):
        nsmap = {'a': act.namespace}

        for elem in act.root.xpath('/a:akomaNtoso/a:components', namespaces=nsmap):
            elem.tag = f'{{{act.namespace}}}attachments'
            # move to last child of act element
            act.main.append(elem)

            for i, att in enumerate(elem.xpath('a:component[a:doc]', namespaces=nsmap)):
                att.tag = f'{{{act.namespace}}}attachment'
                att.set('id', f'att_{i + 1}')

                # heading and subheading
                for heading in att.doc.mainBody.hcontainer.xpath('a:heading | a:subheading', namespaces=nsmap):
                    att.doc.addprevious(heading)

                att.doc.set('name', 'schedule')

                # rewrite ids
                hcontainer = att.doc.mainBody.hcontainer
                id = hcontainer.get('id') + "."
                for child in hcontainer.iterchildren():
                    hcontainer.addprevious(child)
                    rewrite_ids(child, id, '')

                # remove hcontainer
                att.doc.mainBody.remove(hcontainer)


class AKNeId:
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
        "table": (r"\btable(?=\d)", "table_"),
        "blockList": (r"\blist(?=\d)", "list_"),
    }

    def update_xml(self, xml):
        """ Update the xml,
            - first by updating the values of `id` attributes as necessary,
            - and then by replacing all `id`s with `eId`s
        """
        doc = Act(xml)
        self.namespace = doc.namespace

        # basic replacements, e.g. "chapter-" to "chap_"
        for element, patterns in self.basic_replacements.items():
            for node in doc.root.xpath(f"//a:{element}", namespaces={"a": self.namespace}):
                old_id = node.get("id")
                new_id = re.sub(patterns[0], patterns[1], old_id)
                node.set("id", new_id)
                self.update_prefixes(node, old_id, new_id)

        # more complex replacements
        # TODO: simplify the two below (they're very similar)
        # subsections
        for node in doc.root.xpath("//a:subsection", namespaces={"a": self.namespace}):
            old_id = node.get("id")
            # e.g. sec_3a.2A.4.1 --> sec_3a.subsec_2A-4-1
            old_pattern = re.compile(r"^(?P<pre>[^.]+)(?P<post>(\.\d[\dA-Za-z]*)+)")
            match = old_pattern.search(old_id)
            num = (match.group("post").lstrip(".")).replace(".", "-")
            new_id = f"{match.group('pre')}.subsec_{num}"
            node.set("id", new_id)
            self.update_prefixes(node, old_id, new_id)

        # items
        for node in doc.root.xpath("//a:item", namespaces={"a": self.namespace}):
            old_id = node.get("id")
            # e.g. sec_3a.subsec_2-4-1.list_0.b --> sec_3a.subsec_2-4-1.list_0.item_b
            # e.g. sec_3a.subsec_2-4-1.list_0.3.1 --> sec_3a.subsec_2-4-1.list_0.item_3-1
            # or sec_4.subsec_4.list_0.item_c.list_0.i --> sec_4.subsec_4.list_0.item_c.list_0.item_i
            old_pattern = re.compile(r"""
                ^(?P<pre>([^.]+\.)+list_\d+)
                (?P<post>(\.[\da-zA-Z]+)+)$""", re.X)
            match = old_pattern.search(old_id)
            num = (match.group("post").lstrip(".")).replace(".", "-")
            new_id = f"{match.group('pre')}.item_{num}"
            node.set("id", new_id)
            self.update_prefixes(node, old_id, new_id)

        # finally
        # "." separators
        for node in doc.root.xpath("//a:*[@id]", namespaces={"a": self.namespace}):
            old_id = node.get("id")
            if "." in old_id:
                node.set("id", re.sub(r"\.", "__", old_id))

        # replace all `id`s with `eId`s
        for node in doc.root.xpath("//a:*[@id]", namespaces={"a": self.namespace}):
            node.set("eId", node.get("id"))
            del node.attrib["id"]

        return doc.to_xml().decode("utf-8")

    def update_prefixes(self, node, old_id_prefix, new_id_prefix):
        for child in node.xpath(".//a:*[@id]", namespaces={"a": self.namespace}):
            child.set("id", re.sub(rf"^{old_id_prefix}", new_id_prefix, child.get("id")))
