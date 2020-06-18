import logging
import re
from collections import Counter, OrderedDict, defaultdict

from cobalt import FrbrUri, Act
from cobalt.uri import FRBR_URI_RE
from indigo.xmlutils import rewrite_ids
from indigo_api.data_migrations import AKNMigration

log = logging.getLogger(__name__)


class FrbrUriAknPrefix(AKNMigration):
    """ Add (or remove) /akn prefix to FRBR URIs.
    """
    def new_frbr_uri(self, uri, forward, for_work=True):
        """ Sets prefix on uri:
            'akn' if forward is True, None if it's False.
        """
        if not isinstance(uri, FrbrUri):
            uri = FrbrUri.parse(uri)
        uri.prefix = 'akn' if forward else None
        if for_work:
            return uri.work_uri()
        else:
            return uri.expression_uri()

    def migrate_xml(self, document_xml, frbr_uri, forward):
        # Create a cobalt StructuredDocument from the document's existing XML
        cobalt_doc = Act(document_xml)
        # Update the document's FRBR URI in the XML (meta/identification block)
        cobalt_doc.frbr_uri = frbr_uri

        # Add `/akn` prefix (if forward=True; remove if forward=False)
        # to hrefs in <ref> or <passiveRef> AKN elements, e.g.
        # href="/za/act/2012/22" <--> href="/akn/za/act/2012/22"
        for node in cobalt_doc.root.xpath(
                "//a:*[self::a:ref or self::a:passiveRef][starts-with(@href, '/')]",
                namespaces={'a': cobalt_doc.namespace}):
            ref = node.get('href')
            if FRBR_URI_RE.match(ref):
                ref = self.new_frbr_uri(ref, forward)
                node.set('href', ref)

        return cobalt_doc.to_xml().decode('utf-8')


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
            1) \
            .replace(
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            "",
            1) \
            .replace(
            'xmlns="http://www.akomantoso.org/2.0"',
            'xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"',
            1)

        return xml


class AKNeId(AKNMigration):
    """ In a document's XML, translate existing `id` attributes to `eId`
    and follow the new naming and numbering convention
    e.g. "sec_2" instead of "section-2"
    """
    basic_replacements = {
        "chapter": (r"\bchapter-", "chp_"),
        "part": (r"\bpart-", "part_"),
        "subpart": (r"\bsubpart-", "subpart_"),
        "section": (r"\bsection-", "sec_"),
        "article": (r"\barticle-", "article_"),
    }

    add_1_replacements = {
        "table": (re.compile(r"\btable-?\d+$"), "table_"),
        "blockList": (re.compile(r"\blist\d+$"), "list_"),
    }

    complex_replacements = {
        "subsection": "subsec_",
        "item": "item_",
        "paragraph": "para_",
    }

    def components(self, doc):
        """ Get an `OrderedDict` of component name to :class:`lxml.objectify.ObjectifiedElement`
        objects.
        """
        components = OrderedDict()
        for component in doc.root.xpath(
                "./a:act | ./a:act/a:attachments/a:attachment/a:doc | "
                "./a:act/a:components/a:component/a:doc | ./a:components/a:component/a:doc",
                namespaces=self.nsmap):
            if component.tag == f"{{{doc.namespace}}}act":
                components["main"] = component.body
            else:
                name = component.meta.identification.FRBRWork.FRBRthis.get('value').split('/')[-1].lstrip("!")
                while components.get(name) is not None:
                    log.warning(f"Adding '_XXX' to end of component name: {name}")
                    if self.document:
                        log.warning(f"Warning! Document {self.document.pk} has duplicately named schedules. The first schedules named {name} will have to be manually re-parsed (their URI will be wrong until they are).")
                    name += "_XXX"
                    # add "_XXX" to the doc name as well for mappings,
                    # but only for old-style components
                    parent = component.getparent().getparent().getparent()
                    if parent.tag == f"{{{doc.namespace}}}akomaNtoso":
                        component.set("name", name)
                components[name] = component

        return components

    def migrate_act(self, doc, document=None):
        """ Update the xml,
            - first by updating the values of `id` attributes as necessary,
            - and then by replacing all `id`s with `eId`s
        """
        self.nsmap = {"a": doc.namespace}
        self.document = document
        mappings = defaultdict(dict)

        self.paras_to_hcontainers(doc, mappings)
        self.crossheadings_to_hcontainers(doc, mappings)
        self.components_to_attachments(doc, mappings)
        # set FRBR URI on attachments (missed previously because they were components)
        # Note: if there are more than one schedules named e.g. "schedule" only the last one will be updated by this
        doc.frbr_uri = doc.frbr_uri
        self.basics(doc, mappings)
        self.tables_blocklists(doc, mappings)
        self.subsections_items_paras(doc, mappings)
        self.term_ids(doc, mappings)
        self.separators_eids(doc, mappings)
        self.internal_references(doc, mappings)
        self.annotation_anchors(mappings)

        # just for tests
        return mappings

    def safe_update(self, element, mappings, old, new):
        """ Updates ids and mappings:
        - First, check `mappings` for `old`:
            if it's already there, check that it maps to `new`. Log a warning if not.
        - Then, rewrite_ids.
        - If it wasn't already in, update `mappings`.
        """
        if old == new:
            log.warning(f"Not updating unchanged id: {old}")
            return

        if mappings.get("old"):
            if not mappings[old] == new:
                log.warning(f"New id mapping differs from existing: {old} -> {mappings[old]}; ignoring {new}")
            # rewrite ids but don't update mappings
            rewrite_ids(element, old, new)
            return

        mappings.update(rewrite_ids(element, old, new))

    def traverse_mappings(self, old, mappings):
        if old in mappings:
            old = self.traverse_mappings(mappings[old], mappings)

        return old

    def clean_number(self, num):
        # e.g. 1.3.2. / (3) / (dA) / (12 bis)
        return num.strip("().").replace(" ", "").replace(".", "-")

    def get_parent_id(self, node):
        parent = node.getparent()
        if parent is not None:
            parent_id = parent.get("id")
            return parent_id if parent_id and not parent_id.startswith("att_") else self.get_parent_id(parent)

    def paras_to_hcontainers(self, doc, mappings):
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
        for name, root in self.components(doc).items():
            for para in root.xpath('.//a:paragraph[not(a:num)]', namespaces=self.nsmap):
                para.tag = f'{{{doc.namespace}}}hcontainer'
                # new id is based on the number of preceding hcontainer siblings
                num = len(para.xpath('preceding-sibling::a:hcontainer', namespaces=self.nsmap)) + 1
                old_id = para.get('id') or 'paragraph-1'
                new_id = re.sub('paragraph-?(\d+)$', f'hcontainer_{num}', old_id)
                self.safe_update(para, mappings[name], old_id, new_id)

    def crossheadings_to_hcontainers(self, doc, mappings):
        """ Update crossheading ids to hcontainer and number them from 1, e.g.
            <hcontainer id="schedule2.crossheading-0" name="crossheading"> ->
            <hcontainer id="schedule2.hcontainer_1" name="crossheading">
        """
        for name, root in self.components(doc).items():
            for crossheading in root.xpath('.//a:hcontainer[@name="crossheading"]', namespaces=self.nsmap):
                # new id is based on the number of preceding hcontainer siblings
                num = len(crossheading.xpath("preceding-sibling::a:hcontainer", namespaces=self.nsmap)) + 1
                old_id = crossheading.get("id")
                new_id = re.sub("crossheading-(\d+)$", f"hcontainer_{num}", old_id)
                self.safe_update(crossheading, mappings[name], old_id, new_id)

    def components_to_attachments(self, doc, mappings):
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
        self.schedule_mappings = defaultdict(dict)
        for elem in doc.root.xpath('/a:akomaNtoso/a:components', namespaces=self.nsmap):
            elem.tag = f'{{{doc.namespace}}}attachments'
            # move to last child of act element
            doc.main.append(elem)

            for i, att in enumerate(elem.xpath('a:component[a:doc]', namespaces=self.nsmap)):
                att.tag = f'{{{doc.namespace}}}attachment'
                new_id = f'att_{i + 1}'
                att.set("id", new_id)
                old = att.doc.get("name")
                att.doc.set('name', 'schedule')
                self.schedule_mappings[old] = new_id

                # old-style schedules used "article" instead of an hcontainer wrapper
                try:
                    att.doc.mainBody.article.tag = f'{{{doc.namespace}}}hcontainer'
                except AttributeError:
                    pass

                # heading and subheading
                for heading in att.doc.mainBody.hcontainer.xpath('a:heading | a:subheading', namespaces=self.nsmap):
                    att.doc.addprevious(heading)

                # rewrite ids
                hcontainer = att.doc.mainBody.hcontainer
                # e.g. schedule1.
                id = hcontainer.get('id') + "."
                for child in hcontainer.iterchildren():
                    # move the actual xml into the attachment
                    hcontainer.addprevious(child)
                    # update the child's id if it has one
                    if child.get("id"):
                        self.safe_update(child, mappings[old], id, '')
                    else:
                        log.warning(f"Element has no id (taking no action): {new_id} / {hcontainer.get('id')} / {child.tag}")

                # remove hcontainer
                att.doc.mainBody.remove(hcontainer)

        """ Update the prefixes of the anchor ids of all annotations on the document, e.g.
            schedule1/schedule1.paragraph0 -> att_2/schedule1.paragraph0
            schedule1/section-1 -> att_2/section-1
        """
        if self.document:
            for annotation in self.document.annotations.all():
                if "/" in annotation.anchor_id:
                    pre, post = annotation.anchor_id.split("/", 1)
                    new_pre = self.schedule_mappings[pre]
                    if not new_pre:
                        log.warning(f"Not updating annotation prefix: {pre}")
                        continue
                    annotation.anchor_id = f"{new_pre}/{post}"
                    annotation.save()

    def basics(self, doc, mappings):
        for name, root in self.components(doc).items():
            for element, (pattern, replacement) in self.basic_replacements.items():
                for node in root.xpath(f".//a:{element}", namespaces=self.nsmap):
                    old_id = node.get("id")
                    new_id = re.sub(pattern, replacement, old_id)
                    self.safe_update(node, mappings[name], old_id, new_id)

    def tables_blocklists(self, doc, mappings):
        for name, root in self.components(doc).items():
            for element, (pattern, replacement) in self.add_1_replacements.items():
                counter = Counter()
                for node in root.xpath(f".//a:{element}", namespaces=self.nsmap):
                    # default to empty string if no current id
                    old_id = node.get("id", "")
                    prefix = self.get_parent_id(node)
                    # the num for this term depends on the number of preceding terms with the same prefix
                    counter[prefix] += 1
                    new = replacement + str(counter[prefix])
                    # if no current id, generate one now
                    new_id = re.sub(pattern, new, old_id) or new
                    self.safe_update(node, mappings[name], old_id, new_id)

    def subsections_items_paras(self, doc, mappings):
        for name, root in self.components(doc).items():
            for element, replacement in self.complex_replacements.items():
                for node in root.xpath(f".//a:{element}", namespaces=self.nsmap):
                    old_id = node.get("id")
                    # note: all subsections and items should have <num>s in current documents
                    # and all unnumbered paragraphs will have been taken care of by paras_to_hcontainers
                    # but some historical documents have unnumbered subsections instead of unnumbered paragraphs; they'll just get skipped
                    if self.document:
                        num = node.num.text
                    else:
                        try:
                            num = node.num.text
                        except AttributeError as e:
                            log.warning(f"Subsection without a <num> (taking no action) in {old_id}: {e}")
                            break

                    num = self.clean_number(num)
                    new_id = replacement + num
                    prefix = self.get_parent_id(node)
                    if prefix:
                        new_id = f"{prefix}.{new_id}"
                    self.safe_update(node, mappings[name], old_id, new_id)

    def term_ids(self, doc, mappings):
        for name, root in self.components(doc).items():
            counter = Counter()
            for node in root.xpath('.//a:term', namespaces=self.nsmap):
                old_id = node.get('id')
                prefix = self.get_parent_id(node)
                # the num for this term depends on the number of preceding terms with the same prefix
                counter[prefix] += 1
                new_id = f'term_{counter[prefix]}'
                if prefix:
                    new_id = f'{prefix}__{new_id}'
                self.safe_update(node, mappings[name], old_id, new_id)

    def separators_eids(self, doc, mappings):
        for name, root in self.components(doc).items():
            for node in root.xpath(".//a:*[@id]", namespaces=self.nsmap):
                old_id = node.get("id")

                if "." in old_id:
                    new_id = old_id.replace(".", "__")
                    node.set("id", new_id)
                    mappings[name].update({old_id: new_id})

        # all ids become eIds, don't need to be tracked in `mappings`
        for node in doc.root.xpath("//a:*[@id]", namespaces=self.nsmap):
            node.set("eId", node.get("id"))
            del node.attrib["id"]

    def internal_references(self, doc, mappings):
        """ Update all internal references on the document.
        e.g. <ref href="#section-5">section 5</ref>
        ->   <ref href="#sec_5">section 5</ref>
        """
        if self.document:
            for name, root in self.components(doc).items():
                for node in root.xpath(".//a:ref[starts-with(@href, '#')]", namespaces={"a": doc.namespace}):
                    ref = node.get("href").lstrip("#")
                    new_ref = self.traverse_mappings(ref, mappings[name])

                    if new_ref == ref:
                        # we're likely in a schedule and talking about a section in main
                        new_ref = self.traverse_mappings(ref, mappings["main"])

                    if new_ref == ref:
                        # doesn't point at anything
                        log.warning(f"Not updating reference: {ref}")
                        break

                    node.set("href", f"#{new_ref}")

    def annotation_anchors(self, mappings):
        """ Update the anchor ids of all annotations on the document.
            Assume that the prefix (if any) has already been updated.
            e.g. att_2/schedule1.paragraph0 -> att_2/hcontainer_3
                 att_2/section-1 -> att_2/sec_1
        """
        if self.document:
            for annotation in self.document.annotations.all():
                old_anchor = annotation.anchor_id
                if "/" in old_anchor:
                    # att_2/schedule2.crossheading-1
                    pre, post = old_anchor.split("/", 1)
                    old_pre = None
                    for before, after in self.schedule_mappings.items():
                        if pre == after:
                            old_pre = before

                    new_post = self.traverse_mappings(post, mappings[old_pre])
                    annotation.anchor_id = f"{pre}/{new_post}"

                else:
                    annotation.anchor_id = self.traverse_mappings(old_anchor, mappings["main"])

                if annotation.anchor_id == old_anchor:
                    log.warning(f"Not updating annotation anchor id: {old_anchor}")
                    continue

                annotation.save()


class AKN3Laggards(AKNMigration):
    def migrate_act(self, doc):
        # this forces Cobalt to ensure missing FRBR URI elements are added
        doc.frbr_uri = doc.frbr_uri

        self.migrate_ids(doc)
        self.add_names(doc)
        self.add_references_source(doc)
        self.remove_empty_lifecycle(doc)

    def remove_akn2_namespaces(self, xml):
        """ Some elements have explicit AKN2 namespaces. Get rid of them so they default to AKN3.
        """
        return xml.replace(' xmlns="http://www.akomantoso.org/2.0"', '')

    def migrate_ids(self, doc):
        """ Rename remaining id attributes that have been introduced by Cobalt during the AKN3 transition.

        See https://github.com/laws-africa/cobalt/issues/37
        """
        for node in doc.root.xpath("//a:*[@id]", namespaces={'a': doc.namespace}):
            node.set("eId", node.get("id"))
            del node.attrib["id"]

    def add_names(self, doc):
        """ Move name attributes for appropriate elements.

        See https://github.com/laws-africa/indigo/issues/1090
        """
        for node in doc.root.xpath("//a:act[not(@name)]", namespaces={'a': doc.namespace}):
            node.set('name', 'act')

        for node in doc.root.xpath("//a:FRBRalias[not(@name)]", namespaces={'a': doc.namespace}):
            node.set('name', 'title')

        for node in doc.root.xpath("//a:hcontainer[not(@name)]", namespaces={'a': doc.namespace}):
            node.set('name', 'hcontainer')

    def remove_empty_lifecycle(self, doc):
        """ Remove empty lifecycle elements

        See https://github.com/laws-africa/cobalt/issues/37
        """
        for node in doc.root.xpath("//a:lifecycle[not(*)]", namespaces={'a': doc.namespace}):
            node.getparent().remove(node)

    def add_references_source(self, doc):
        """ Add source attribute to references

        See https://github.com/laws-africa/cobalt/issues/37
        """
        for node in doc.root.xpath("//a:references[not(@source)]", namespaces={'a': doc.namespace}):
            node.set('source', '#cobalt')
