import os.path
import re
from collections import defaultdict
from difflib import HtmlDiff, Differ

from lxml import etree

from bluebell.parser import AkomaNtosoParser
from bluebell.xml import IdGenerator, XmlGenerator
from cobalt import FrbrUri
from cobalt.akn import get_maker, AKN_NAMESPACES, DEFAULT_VERSION, AkomaNtosoDocument
from cobalt.schemas import get_schema, validate_xml
from indigo_api.data_migrations import DataMigration
from indigo_api.models import Annotation


AKN_HIERARCHICAL = [
    'alinea', 'article', 'book', 'chapter', 'clause', 'division', 'indent', 'level', 'list',
    'paragraph', 'part', 'point', 'proviso', 'rule', 'section',
    'subchapter', 'subclause', 'subdivision', 'sublist', 'subparagraph', 'subpart', 'subrule',
    'subsection', 'subtitle', 'title', 'tome', 'transitional',
]


class SlawToBluebell(DataMigration):
    """ Migrate slaw XML to bluebell XML
    """
    xslt_filename = os.path.join(os.path.dirname(__file__), 'slaw-to-bluebell.xslt')
    diff_xslt_filename = os.path.join(os.path.dirname(__file__), 'for-comparison.xslt')
    unpretty_xslt_filename = os.path.join(os.path.dirname(__file__), 'unpretty.xslt')

    def __init__(self):
        self.xslt = etree.XSLT(etree.parse(self.xslt_filename))
        self.diff_xslt = etree.XSLT(etree.parse(self.diff_xslt_filename))
        self.unpretty_xslt = etree.XSLT(etree.parse(self.unpretty_xslt_filename))
        self.ns = AKN_NAMESPACES[DEFAULT_VERSION]
        self.schema = get_schema(self.ns, strict=False)
        self.maker = get_maker()
        self.id_generator = IdGenerator()
        self.eid_mappings = {}

    def validate(self, xml):
        return validate_xml(etree.fromstring(xml), self.schema)

    def should_migrate(self, document):
        """ Does this document need to be migrated?
        """
        # we don't have a mechanism for safely identifying old documents that must be migrated. However,
        # migration is idempotent, so simply always migrate
        return True

    def migrate_document(self, document):
        self.ns = document.doc.namespace
        root = etree.fromstring(document.document_xml)
        changed, root = self.migrate_xml(root)
        if changed:
            document.reset_xml(etree.tostring(root, encoding='unicode'), from_model=True)
            return True

    def migrate_work_expression(self, expr):
        self.ns = expr.doc.namespace
        root = etree.fromstring(expr.document_xml)
        changed, root = self.migrate_xml(root)
        if changed:
            # this mimics document.reset_xml and ensures that some metadata is correctly updated in the new XML
            xml = etree.tostring(root, encoding='unicode')
            doc = expr.cobalt_class(xml)
            doc.frbr_uri = expr.expression_frbr_uri
            doc.expression_date = expr.expression_date
            expr.document_xml = doc.to_xml().decode('utf-8')
            return True

    def migrate_annotations(self, document):
        count = 0
        for old, new in self.eid_mappings.items():
            if old != new:
                count += Annotation.objects.filter(document_id=document.id, anchor_id=old).update(anchor_id=new)
        return count

    def preclean_xml_string(self, xml):
        # replace newlines with a space
        xml = re.sub(r'\s*[\n\r]+\s*', ' ', xml)
        # condense multiple br's
        xml = re.sub('(<br/>)(\s*<br/>)*', '<br/>', xml)
        # unprettyify
        return self.unpretty(xml)

    def migrate_xml(self, xml):
        xml = etree.tostring(xml, encoding='unicode')
        xml = self.preclean_xml_string(xml)
        xml = etree.fromstring(xml)

        # apply xslt
        xml = etree.tostring(self.xslt(xml), encoding='unicode')
        xml = etree.fromstring(xml)

        self.table_br_to_p(xml, 'br')
        self.table_br_to_p(xml, 'eol')
        self.table_nuke_blank_ps(xml)
        self.migrate_attachment_names_and_alias(xml)
        self.fix_crossheadings(xml)

        BlocklistToPara().migrate_xml(xml)
        DefsParaToBlocklist().migrate_xml(xml)

        self.normalise(xml)
        self.eid_mappings = self.id_generator.rewrite_all_eids(xml)
        self.update_img_src_and_href(xml)
        self.update_internal_refs(xml)
        self.update_source(xml)

        return True, xml

    def table_br_to_p(self, xml, tag_name):
        """ Change br's (or eol's) in p's to consecutive p's in tables, going backwards.

            <p>foo<br/>bar<br/>with a <term>term</term></p>
        becomes
            <p>foo</p>
            <p>bar</p>
            <p>with a <term>term</term></p>

        and

            <p>
              start
              <b>
                bold
                <i>italics <br/> br tail</i>
                ital tail
              </b>
              bold tail
            </p>

        becomes

            <p>
              start
              <b>
                bold
                <i>italics </i>
              </b>
            </p>
            <p>
              <b>
                <i> br tail</i>
                ital tail
              </b>
              bold tail
            </p>
        """
        for tag_name in reversed(xml.xpath(f'//a:*[self::a:td or self::a:th]/a:p//a:{tag_name}[not(ancestor::a:remark)]', namespaces={'a': self.ns})):
            # duplicate ancestors on the way back up to containing p, so that b and i get included
            new_el = None
            el = tag_name
            prev_new_el = None
            while el.tag != f'{{{self.ns}}}p':
                parent = el.getparent()
                tag = parent.tag.split('}', 1)[1]
                new_el = getattr(self.maker, tag)()

                if prev_new_el is not None:
                    new_el.append(prev_new_el)
                    # move over the tail
                    prev_new_el.tail = el.tail
                else:
                    # move over the tail
                    new_el.text = el.tail
                el.tail = None

                # move following siblings
                for sibling in el.itersiblings():
                    new_el.append(sibling)

                prev_new_el = new_el
                el = el.getparent()

            tag_name.getparent().remove(tag_name)
            el.addnext(new_el)

    def table_nuke_blank_ps(self, xml):
        """ remove empty p tags in tables, unless they don't have siblings
        """
        for p in xml.xpath('//a:*[self::a:td or self::a:th]/a:p[not(node())]', namespaces={'a': self.ns}):
            if p.getprevious() is not None or p.getnext() is not None:
                parent = p.getparent()
                parent.remove(p)

    def migrate_attachment_names_and_alias(self, xml):
        """ Rename attachments correctly in their FRBR URIs:

        <FRBRthis value="/akn/za/act/2016/6azu7/!schedule2"/> becomes
        <FRBRthis value="/akn/za/act/2016/6azu7/!schedule_2"/>

        And ensure attachment FRBRaliases use all text from headings
        """
        counter = defaultdict(lambda: 0)
        for doc in xml.xpath('//a:attachment/a:doc', namespaces={'a': self.ns}):
            parent = doc.getparent().xpath('ancestor::a:attachment/a:doc/a:meta/a:identification/a:FRBRWork/a:FRBRthis', namespaces={'a': self.ns})
            prefix = ''
            if parent:
                prefix = FrbrUri.parse(parent[0].attrib['value']).work_component + '/'

            # establish the work component for this attachment
            name = doc.attrib['name']
            counter[name] += 1
            work_component = f'{prefix}{name}_{counter[name]}'

            # set it
            for part in ['a:FRBRWork', 'a:FRBRExpression', 'a:FRBRManifestation']:
                for element in doc.xpath('./a:meta/a:identification/' + part + '/a:FRBRthis', namespaces={'a': self.ns}):
                    frbr_uri = FrbrUri.parse(element.attrib['value'])
                    frbr_uri.work_component = work_component
                    element.attrib['value'] = {
                        'a:FRBRWork': lambda: frbr_uri.work_uri(),
                        'a:FRBRExpression': lambda: frbr_uri.expression_uri(),
                        'a:FRBRManifestation': lambda: frbr_uri.manifestation_uri(),
                    }[part]()

            # set alias if the heading has complex content
            att = doc.getparent()
            heading = att.find(f'{{{self.ns}}}heading')
            if heading is not None and list(heading.itertext()):
                alias = doc.xpath('./a:meta/a:identification/a:FRBRWork/a:FRBRalias', namespaces={'a': self.ns})
                alias[0].set('value', ''.join(heading.itertext()))

        return xml

    def normalise(self, xml):
        """ Basic normalisations that copy bluebell
        """
        XmlGenerator().normalise(xml)
        for elem in xml.xpath('//a:*[self::a:heading or self::a:listIntroduction][not(node())]', namespaces={'a': xml.nsmap[None]}):
            elem.getparent().remove(elem)

        # strip whitespace at the start and end of p tags
        for p in xml.xpath('//a:p', namespaces={'a': xml.nsmap[None]}):
            kids = list(p)
            if p.text:
                p.text = p.text.lstrip()
                if not kids:
                    # no kids, strip end of text too
                    p.text = p.text.rstrip()

            if kids:
                kid = kids[-1]
                if kid.tail:
                    kid.tail = kid.tail.rstrip()

        # strip whitespace at the start and end of attributes; normalise to single spaces within
        # TODO: narrow xpath to only grab elements that have a space in any of their attributes?
        for el in xml.xpath('//a:*', namespaces={'a': xml.nsmap[None]}):
            for a, val in el.attrib.items():
                # skip value and src, as these won't be cleaned up by bluebell
                if a not in ['src', 'value']:
                    newval = re.sub(r'\s{2,}', ' ', val.lstrip().rstrip())
                    if val != newval:
                        el.set(a, newval)

        # strip whitespace just after br's in multi-line remarks
        for br in xml.xpath('//a:remark/a:br', namespaces={'a': xml.nsmap[None]}):
            if br.tail:
                br.tail = br.tail.lstrip()

        # remove empty p tags at start and end of table cells
        for p in xml.xpath('//a:*[self::a:th or self::a:td]/a:p[not(normalize-space(.)) and ('
                           '(not(preceding-sibling::a:*) and following-sibling::a:*) or '
                           '(preceding-sibling::a:* and not(following-sibling::a:*)))]',
                           namespaces={'a': self.ns}):
            if not list(p.getchildren()):
                p.getparent().remove(p)

    def fix_crossheadings(self, xml):
        """ Left and right strip crossheadings, and merge adjacent crossHeadings in hcontainers
        """
        # we don't recurse deeply, just check the top-level text
        for heading in xml.xpath('//a:crossHeading', namespaces={'a': self.ns}):
            if heading.text:
                heading.text = heading.text.lstrip()
            if not list(heading):
                # no children, strip on the right, too
                heading.text = heading.text.rstrip()

        for heading in xml.xpath('//a:hcontainer/a:crossHeading', namespaces={'a': self.ns}):
            parent = heading.getparent()
            prev = parent.getprevious()
            if prev is not None and prev.tag == f'{{{self.ns}}}hcontainer':
                prev_headings = prev.findall(f'{{{self.ns}}}crossHeading')
                if prev_headings:
                    # add after last preceding crossHeading
                    prev_headings[-1].addnext(heading)
                    parent.getparent().remove(parent)

    def update_internal_refs(self, xml):
        """ Update internal references in XML based on self.eid_mappings.

            <ref href="#sec_1">section 1</ref> --> <ref href="#chp_1__sec_1">section 1</ref>
        """
        for ref in xml.xpath('//a:ref[starts-with(@href, "#")]', namespaces={'a': self.ns}):
            old_ref = ref.attrib.get('href', '').lstrip('#')
            ref.set('href', f'#{self.eid_mappings.get(old_ref, old_ref)}')

    def update_img_src_and_href(self, xml):
        """ Update img/@src and ref/@href to replace spaces with %20.
        """
        for ref in xml.xpath('//a:img[@src]', namespaces={'a': self.ns}):
            ref.set('src', ref.get('src').replace(' ', '%20'))

        for ref in xml.xpath('//a:ref[@href]', namespaces={'a': self.ns}):
            ref.set('href', ref.get('href').replace(' ', '%20'))

    def update_source(self, xml):
        """ Update @source="..." to ensure it matches the platform settings. Also updates TLCOrganisation if necessary.
        """
        id_ = '#' + AkomaNtosoDocument.source[1]
        deleted_sources = set()

        for elem in xml.xpath('//a:identification[@source] | //a:lifecycle[@source] | //a:references[@source]', namespaces={'a': self.ns}):
            source = elem.get('source')
            if source and source.startswith('#') and source != id_:
                deleted_sources.add(source[1:])
                elem.set('source', id_)

        for org in xml.xpath('//a:TLCOrganization', namespaces={'a': self.ns}):
            if org.get('eId', None) in deleted_sources:
                org.getparent().remove(org)

        # ensure there is a TLCOrganisation for indigo
        refs = xml.xpath('//a:references', namespaces={'a': self.ns})[0]
        for org in refs.xpath('./a:TLCOrganization', namespaces={'a': self.ns}):
            if org.get('eId') == AkomaNtosoDocument.source[1]:
                org.set('href', AkomaNtosoDocument.source[2])
                org.set('showAs', AkomaNtosoDocument.source[0])
                break
        else:
            # didn't exist, add it
            org = self.maker('TLCOrganization', showAs=AkomaNtosoDocument.source[0], eId=AkomaNtosoDocument.source[1],
                             href=AkomaNtosoDocument.source[2])
            refs.insert(0, org)

        # if the source is not Indigo-Platform, ensure that legacy entry is removed
        if id_ != '#Indigo-Platform':
            for org in xml.xpath('//a:TLCOrganization[@eId="Indigo-Platform"]', namespaces={'a': self.ns}):
                org.getparent().remove(org)

        # remove legacy Cobalt organisation
        for org in xml.xpath('//a:references/a:TLCOrganization[@href="https://github.com/laws-africa/cobalt"]', namespaces={'a': self.ns}):
            parent = org.getparent()
            parent.remove(org)

        # remove empty references
        for ref in xml.xpath('//a:references[not(node())]', namespaces={'a': self.ns}):
            ref.getparent().remove(ref)

    def quality_diff_xml(self, first_xml, second_xml):
        """ Compare two migrated documents, accounting for expected differences.
        """
        first_xml = self.prepare_for_diff(first_xml)
        second_xml = self.prepare_for_diff(second_xml)

        if first_xml == second_xml:
            return None

        first_xml = first_xml.splitlines(keepends=True)
        second_xml = second_xml.splitlines(keepends=True)

        return Differ().compare(first_xml, second_xml)

    def prepare_for_diff(self, xml_str):
        """ Prepare this XML for comparison, taking into account known differences.
        Returns a canonicalised, pretty-printed XML string.
        """
        xml = etree.fromstring(xml_str)
        # apply xslt to prepare for comparison, removing certain things that make differences harder to visualise
        xml = etree.tostring(self.diff_xslt(xml), encoding='unicode')
        # canonicalise and pretty-print
        return pretty_c14n(xml)

    def stability_diff(self, doc):
        """ Return a diff (if any) between the migrated XML and re-parsed migrated XML.
        """
        original_xml = doc.document_xml
        self.reparse_as_bluebell(doc)

        # TLCTerms are lost during reparsing, so remove them from the original content
        original_xml = etree.fromstring(original_xml)
        for term in original_xml.xpath('//a:TLCTerm', namespaces={'a': original_xml.nsmap[None]}):
            term.getparent().remove(term)
        original_xml = etree.tostring(original_xml, encoding='unicode')
        # replace newlines with spaces when calculating diffs, because bluebell will do the same
        xml = re.sub(r'\s*[\n\r]+\s*', ' ', original_xml)

        # some old documents are pretty-printed, so un-pretty before comparing
        migrated_xml = pretty_c14n(self.unpretty(original_xml))
        reparsed_xml = pretty_c14n(doc.document_xml)

        # put the original content back
        doc.document_xml = original_xml

        if migrated_xml == reparsed_xml:
            return None

        return diff_table(migrated_xml, reparsed_xml, "Migrated XML", "Reparsed Migrated XML")

    def content_fingerprint_diff(self, old_xml, new_xml):
        old_fp = self.content_fingerprint(old_xml)
        new_fp = self.content_fingerprint(new_xml)

        if old_fp == new_fp:
            return None

        return diff_table(old_fp, new_fp, "Original fingerprint", "Migrated fingerprint")

    def content_fingerprint(self, xml):
        """ Generate a content fingerprint for this xml.
        """
        xml = self.preclean_xml_string(xml)
        # replace one or more br's with newlines
        xml = re.sub(r'(<br/>)+', '\n', xml)
        # replace one or more eol's with newlines
        xml = re.sub(r'(<eol/>)+', '\n', xml)
        xml = etree.fromstring(xml)

        # replace images with text
        for img in xml.xpath('//a:img', namespaces={'a': self.ns}):
            parent = img.getparent()
            s = 'IMG ' + img.get('src').replace(' ', '%20') + (img.tail or '')

            prev = img.getprevious()
            if prev is not None:
                prev.tail = (prev.tail or '') + s
            else:
                parent.text = (parent.text or '') + s

            parent.remove(img)

        # gather all the elements that can contain useful text
        elems = xml.xpath('//a:p | //a:heading | //a:subheading | //a:num | //a:crossHeading | //a:listIntroduction | //a:listWrapUp',
                          namespaces={'a': self.ns})
        # join their texts together
        texts = (''.join(x.xpath('.//text()')) for x in elems)
        text = '\n'.join(x.strip() for x in texts if x)

        # strip leading and trailing whitespace on all lines
        text = re.sub(r'(^\s+)|(\s+$)', '', text, flags=re.MULTILINE)
        return text

    def reparse_as_bluebell(self, doc):
        """ Unparse and then re-parse this document's content as a bluebell document.
        This is only use for comparing differences with the real migration, which is done with XSLT and python.
        """
        parser = AkomaNtosoParser(doc.expression_uri)

        # unparse and re-parse with bluebell
        xml = etree.fromstring(doc.document_xml)
        text = parser.unparse(xml)
        reparsed_xml = parser.parse_to_xml(text, doc.expression_uri.doctype)
        reparsed_xml = etree.tostring(reparsed_xml, encoding='unicode')
        # assign back into the document so title etc. are injected
        doc.reset_xml(reparsed_xml, from_model=True)

    def unpretty(self, xml):
        """ Un-pretty-prints XML.
        """
        return etree.tostring(self.unpretty_xslt(etree.fromstring(xml)), encoding='unicode')


class BlocklistToPara:
    """ Change blockLists to paragraph/subparagraph[/subparagraph].
    """
    def __init__(self):
        self.ns = AKN_NAMESPACES[DEFAULT_VERSION]
        self.maker = get_maker()

    def migrate_xml(self, xml):
        self.blocklist_to_para(xml)
        self.unwrap_hcontainers(xml)
        self.intro_and_wrapup(xml)

    def make_and_insert_hcontainer(self, elem, content):
        m = self.maker
        h = m.hcontainer()
        h.set('name', 'hcontainer')
        h_content = m.content()
        h_content.append(elem)
        h.append(h_content)
        content.addprevious(h)

    def move_to_hcontainer_before_content(self, elem, content):
        """ Looks for an hcontainer immediately preceding content,
            and appends elem to its <content>.
            If there isn't one, create it.
        """
        before_c = content.getprevious()
        if before_c is not None and before_c.tag == f'{{{self.ns}}}hcontainer':
            h_content = before_c.find('a:content', namespaces={'a': self.ns})
            if h_content is not None:
                h_content.append(elem)
            # hcontainer may contain e.g. a crossHeading, not content
            else:
                self.make_and_insert_hcontainer(elem, content)
        else:
            self.make_and_insert_hcontainer(elem, content)

    def deal_with_list_(self, element_name, blocklist, content):
        """ Transforms a <listIntroduction> or <listWrapUp> of a blocklist into a <p> and moves it out into an <hcontainer>/<content> before content.
        """
        elem = blocklist.find(f'a:{element_name}', namespaces={'a': self.ns})
        if elem is not None:
            elem.tag = f'{{{self.ns}}}p'
            self.move_to_hcontainer_before_content(elem, content)

    def unpack_items(self, blocklist, content):
        """ Transforms each <item> in the blocklist into a <paragraph> element,
             puts each child (other than num) into a new <content> inside the renamed item,
             and moves it out before content.
        """
        m = self.maker

        for item in blocklist.xpath('a:item', namespaces={'a': self.ns}):
            item.tag = f'{{{self.ns}}}paragraph'
            new_content = m.content()
            for c in item.iterchildren():
                if c.tag not in [f'{{{self.ns}}}num', f'{{{self.ns}}}heading', f'{{{self.ns}}}subheading']:
                    # delete empty p tags
                    if c.tag != f'{{{self.ns}}}p' or c.text or list(c.getchildren()):
                        new_content.append(c)
                    else:
                        item.remove(c)
            if list(new_content.getchildren()):
                item.append(new_content)
            content.addprevious(item)

    def convert_single_blocklist(self, bl, content):
        self.deal_with_list_('listIntroduction', bl, content)
        self.unpack_items(bl, content)
        self.deal_with_list_('listWrapUp', bl, content)
        assert not list(bl.getchildren())
        # sometimes the parent is mainBody, not content
        parent = bl.getparent()
        parent.remove(bl)

    def first_level_blocklists(self, xml):
        return xml.xpath('//a:content[a:blockList]', namespaces={'a': self.ns})

    def convert_first_level(self, xml):
        """ Converts all <content> elements that have a <blockList> child,
         and all <blockLists> that are the immediate child of mainBody.
            Treats each content element as a whole, because they can include multiple blockList, p, crossHeading, etc elements.
            Any descendant blockLists will be unchanged.
        """
        for content in self.first_level_blocklists(xml):
            for c in content.iterchildren():
                # if it's a blockList, unpack it
                if c.tag == f'{{{self.ns}}}blockList':
                    self.convert_single_blocklist(c, content)
                # otherwise, stick in in an <hcontainer>/<content> before content
                else:
                    self.move_to_hcontainer_before_content(c, content)

            # everything has been moved out; nuke the empty <content>
            parent = content.getparent()
            assert not list(content.getchildren())
            parent.remove(content)

        # unpack blockLists that are immediate children of mainBody
        for blocklist in xml.xpath('//a:mainBody/a:blockList', namespaces={'a': self.ns}):
            self.convert_single_blocklist(blocklist, blocklist)

    def blocklist_to_para(self, xml):
        """ Rewrite <content>/<blockList>s as <paragraph>s and nested <subparagraph>s.
            Move 
            - any preceding <p>s, as well as the <listIntroduction>,
            - any intervening <p>s,
            - the <listWrapUp>, as well as any following <p>s,
            into an <hcontainer>/<content> in the appropriate order.
            Move everything out of <content>.
            TODO: deal with crossHeadings
        """
        # convert all first-level blockLists to paragraphs, until none are left
        while self.first_level_blocklists(xml):
            self.convert_first_level(xml)

        # convert all para/para into para/subpara
        for para in xml.xpath('//a:paragraph[ancestor::a:paragraph]', namespaces={'a': self.ns}):
            para.tag = f'{{{self.ns}}}subparagraph'

    def unwrap_hcontainers(self, xml):
        """ Moves <paragraph>s as well as any siblings out of their parent <hcontainer>s, and removes the empty shell.
            Moves <p>s in <hcontainer>/<content> out if they're the direct child of mainBody.
        TODO: merge adjacent hcontainers?
        """
        for hcontainer in xml.xpath('//a:hcontainer[a:paragraph]', namespaces={'a': self.ns}):
            for c in hcontainer.iterchildren():
                hcontainer.addprevious(c)

            assert not list(hcontainer.getchildren())
            parent = hcontainer.getparent()
            parent.remove(hcontainer)

        for content in xml.xpath('//a:mainBody/a:hcontainer/a:content', namespaces={'a': self.ns}):
            hcontainer = content.getparent()
            for c in content.iterchildren():
                hcontainer.addprevious(c)

            assert not list(content.getchildren())
            hcontainer.remove(content)
            assert not list(hcontainer.getchildren())
            parent = hcontainer.getparent()
            parent.remove(hcontainer)

    def intro_and_wrapup(self, xml):
        """ Transforms first and last <hcontainer>s into <intro> and <wrapUp>.
        """
        for hcontainer in xml.xpath('//a:hcontainer[not(parent::a:body | parent::a:mainBody)]', namespaces={'a': self.ns}):
            content = hcontainer.find('a:content', namespaces={'a': self.ns})
            if content is None:
                continue

            # first of +1?
            prev_sib = hcontainer.getprevious()
            next_sib = hcontainer.getnext()
            if (prev_sib is None or prev_sib.tag in [f'{{{self.ns}}}num', f'{{{self.ns}}}heading', f'{{{self.ns}}}subheading']) and next_sib is not None:
                content.tag = f'{{{self.ns}}}intro'
                hcontainer.addprevious(content)
                assert not list(hcontainer.getchildren())
                parent = hcontainer.getparent()
                parent.remove(hcontainer)

            # last of +1, and previous isn't now <intro>?
            elif next_sib is None:
                prev_sib = hcontainer.getprevious()
                if prev_sib is not None and prev_sib.tag != f'{{{self.ns}}}intro':
                    content.tag = f'{{{self.ns}}}wrapUp'
                    hcontainer.addprevious(content)
                    assert not list(hcontainer.getchildren())
                    parent = hcontainer.getparent()
                    parent.remove(hcontainer)


class DoNotMigrate(Exception):
    msg = ''

    def __init__(self, **kwargs):
        self.msg = kwargs.get('msg')


class DefsParaToBlocklist:
    """ Change paragraphs/subparagraphs (back) into blockLists for defined terms.
        This is designed to be run immediately after the BlocklistToPara migration during the SlawToBluebell migration.
        Works on the following language documents so far:
        - English
        - Afrikaans
        (Update self.heading_re to add more headings / in more languages.)
    """

    def __init__(self):
        self.maker = get_maker()
        self.ns = AKN_NAMESPACES[DEFAULT_VERSION]
        self.nsmap = {'a': self.ns}
        # these are basically interchangeable so we should look for both
        para_subpara = ['paragraph', 'subparagraph']

        # a migration is needed if any element containing a def that isn't a (sub)paragraph is followed by a (sub)paragraph
        self.needs_migration_xpath = etree.XPath(
            '|'.join(f'//a:*[not(self::a:{x})][descendant::a:def][following-sibling::a:{x}]' for x in para_subpara),
            namespaces=self.nsmap)

        # the element to be migrated is an intro or hcontainer followed by a (sub)paragraph
        para_subpara_follows = '|'.join(f'following-sibling::a:{x}' for x in para_subpara)
        self.do_migration_xpath = etree.XPath(
            f'a:intro[a:p][{para_subpara_follows}]|'
            f'a:hcontainer[a:content/a:p][{para_subpara_follows}]',
            namespaces=self.nsmap)

        # defs section: a section containing at least one def
        self.potential_defs_elements_xpath = etree.XPath('//a:section[descendant::a:def]', namespaces=self.nsmap)
        # defs subsection: a subsection (within a defs section) containing at least one def
        self.subsection_xpath = etree.XPath('a:subsection[descendant::a:def]', namespaces=self.nsmap)
        # definitions as paragraphs can be in a defs section or subsection
        para_subpara_def = [f'a:{x}[descendant::a:def]' for x in para_subpara]
        subsec_para_subpara_def = '|'.join(f'a:subsection/{x}' for x in para_subpara_def)
        self.defs_para_xpath = etree.XPath(
            '|'.join(['|'.join(para_subpara_def), subsec_para_subpara_def]),
            namespaces=self.nsmap)

        self.para_subpara_tags = [f'{{{self.ns}}}{x}' for x in para_subpara]
        # don't try to accommodate (sub)paragraphs with headings
        self.para_subpara_xpath = etree.XPath('|'.join(f'a:{x}[not(a:heading)]' for x in para_subpara), namespaces=self.nsmap)
        self.hcontainer_xpath = etree.XPath('a:hcontainer', namespaces=self.nsmap)
        self.definition_xpath = etree.XPath('a:def', namespaces=self.nsmap)

    def migrate_xml(self, xml):
        """ Rewrite <p> followed by <paragraph>s as <blockList>s in guessed-at definitions elements.
            1. Get definitions elements.
            2. Transform each <p> followed by <(sub)paragraph>s into a <blockList> (including nested <(sub)paragraph>s).
            3. Reconfigure the structure of any transformed parent elements to be:
                <element>/<content>/<p>|<blockList>
        """
        defs_elements = list(self.definition_elements(xml))
        for defs in defs_elements:
            self.process_defs(defs)

    def definition_elements(self, xml):
        """ Yield sections that definitely contain at least one <def>.
            Yield subsections within the sections instead if they contain at least one <def>.
            If each definition is a (sub)paragraph, yield each of those that needs to be converted instead.
        """
        for elem in self.potential_defs_elements_xpath(xml):
            # look for paragraphs first
            paras = self.defs_para_xpath(elem)
            for para in paras:
                if self.do_migration_xpath(para):
                    yield para

            # then subsections
            if not paras:
                subsections = self.subsection_xpath(elem)
                for subsection in subsections:
                    if self.do_migration_xpath(subsection):
                        yield subsection

                # and ultimately the section
                if not subsections and self.do_migration_xpath(elem):
                    yield elem

    def process_defs(self, defs):
        """ Turn all relevant (sub)paragraphs into blockLists:
            - For each <intro> or <hcontainer> followed by <(sub)paragraph>s,
               the final <p> becomes a <listIntroduction> in a new <blockList>,
               and each subsequent <(sub)paragraph> becomes an item in that <blockList>.
            - Fix the structure so that it's just one <content> containing <p>s and <blockList>s.
        """
        # rewrite the last <p> in each intro/hcontainer to be a blockList
        for container in self.do_migration_xpath(defs):
            self.make_blocklist_in(container)
        # now fix the structure of the parent element
        self.make_and_unpack_into_content(defs)

    def make_blocklist_in(self, container):
        """ Transforms the final <p> in the container into a listIntroduction,
             transforms the following <(sub)paragraph>s into <item>s (and unpacks their <content>),
             and makes a blockList where the <p> is and moves the <listIntroduction> and <item>s into it.
        """
        new_blocklist = self.maker.blockList()
        # container.xpath returns a list
        p_listintro = container.xpath('a:p[last()]|a:content/a:p[last()]', namespaces=self.nsmap)[-1]
        # transfer the refersTo attribute from the <p> to the <blockList>
        self.transfer_refersto(p_listintro, new_blocklist)
        p_listintro.tag = f'{{{self.ns}}}listIntroduction'
        p_listintro.addprevious(new_blocklist)
        new_blocklist.append(p_listintro)
        for next_sib in container.itersiblings():
            # we've reached the end of the (sub)paragraphs we're interested in
            if next_sib.tag not in self.para_subpara_tags:
                break
            self.process(next_sib, new_blocklist)

    def process(self, elem, bl):
        """ Convert the element into a blockList,
             but if it contains (sub)paragraphs sort those out first.
        """
        if self.para_subpara_xpath(elem):
            self.convert_children(elem)
        self.convert_into_blocklist_item(elem, bl)

    def convert_children(self, elem):
        """ For elements that have hierarchical children:
            - Create a <blockList> that will be the new home for the intro / hier / wrapUp
            - Unwrap the <intro> and <wrapUp> (both optional)
            - Send the hierarchical children for processing.
        """
        # skip if there are hcontainers between the (sub)paragraph children; they're rare and risky to work with
        if self.hcontainer_xpath(elem):
            raise DoNotMigrate(msg=f'hcontainers amongst children are not supported; see {elem.get("eId")}')

        blocklist = self.maker.blockList()
        bl_added = False

        intro = elem.find('a:intro', namespaces=self.nsmap)
        if intro is not None:
            # add the blockList before the intro
            intro.addprevious(blocklist)
            bl_added = True
            # turn it into a listIntroduction and graduate its <p>
            self.unpack(intro, blocklist, 'listIntroduction')

        for para in self.para_subpara_xpath(elem):
            if not bl_added:
                # add the blockList before the first paragraph if there was no intro
                para.addprevious(blocklist)
                bl_added = True
            self.process(para, blocklist)

        wrap = elem.find('a:wrapUp', namespaces=self.nsmap)
        if wrap is not None:
            # turn it into a listWrapUp and graduate its <p>
            self.unpack(wrap, blocklist, 'listWrapUp')

    def unpack(self, elem, bl, tag):
        """ Assuming one child that is a <p>, add its content to the element, nuking its wrapper.
            Multi-line and complex intros and wraps are not supported.
        """
        children = elem.getchildren()
        if not len(children) == 1:
            raise DoNotMigrate(msg=f'Multi-line intros and wraps are not supported; see {children[-1].get("eId")}')
        child = children[0]
        if not child.tag == f'{{{self.ns}}}p':
            raise DoNotMigrate(msg=f'Complex intros and wraps are not supported; see {child.get("eId")}')

        child.tag = f'{{{self.ns}}}{tag}'
        # transfer the refersTo attribute from the <p> to the <blockList>
        self.transfer_refersto(child, bl)
        bl.append(child)
        self.nuke(elem)

    def nuke(self, elem):
        """ Helper method: Asserts element no longer has children and removes it.
        """
        assert not list(elem.getchildren())
        parent = elem.getparent()
        parent.remove(elem)

    def graduate(self, elem, into):
        """ Helper method: Sticks the children of `elem` into `into`, and nukes `elem` itself.
        """
        for c in elem.iterchildren():
            into.append(c)
        self.nuke(elem)

    def transfer_refersto(self, elem, bl):
        """ Helper method: Removes the refersTo attribute from an element;
            if it exists, add it to the blockList.
            If it doesn't exist, look for one in a <def> inside the element.
        """
        refers_to = elem.attrib.pop('refersTo', None)
        if not refers_to:
            definition = self.definition_xpath(elem)
            if definition:
                refers_to = definition[0].get('refersTo')
        if refers_to:
            bl.attrib['refersTo'] = refers_to

    def convert_into_blocklist_item(self, elem, blocklist):
        """ For elements that don't have hierarchical children:
            - Convert the element into an <item>
            - Graduate its <content> and nuke the wrapper
            - Ignore other children, e.g. <num>, <blockList>
            - Append it to its <blockList>.
        """
        elem.tag = f'{{{self.ns}}}item'

        for c in elem.iterchildren():
            if c.tag == f'{{{self.ns}}}content':
                self.graduate(c, elem)

            blocklist.append(elem)

    def make_and_unpack_into_content(self, elem):
        """ Given an element that contains any of the elements listed below,
            - Create a <content> to house all block elements
            - Move all block elements into this new home.
            (Leave num, heading, and subheading where they are.)
        """
        anything_else = elem.xpath('a:*[not('
                                   'self::a:num|self::a:heading|self::a:subheading|'
                                   'self::a:intro|self::a:hcontainer|self::a:wrapUp|'
                                   'self::a:blockList)]', namespaces=self.nsmap)
        if anything_else:
            raise DoNotMigrate(msg=f"woah! there's other stuff here: {[a.get('eId') for a in anything_else]}")

        for c in elem.iterchildren():
            # ignore num, heading, subheading
            if c.tag in [f'{{{self.ns}}}num', f'{{{self.ns}}}heading', f'{{{self.ns}}}subheading']:
                continue

            # make and put a <content> before the first child that isn't num / heading / subheading
            content = c.getprevious()
            if content is None or content.tag != f'{{{self.ns}}}content':
                content = self.maker.content()
                c.addprevious(content)

            # if it's a blocklist, move it as is
            if c.tag == f'{{{self.ns}}}blockList':
                content.append(c)
                continue

            # otherwise, stick the child's children (or grandchildren if the child is a <content>)
            # into the new <content>
            for cc in c.iterchildren():
                if cc.tag == f'{{{self.ns}}}content':
                    self.graduate(cc, content)
                else:
                    content.append(cc)

            # nuke e.g. hcontainer
            self.nuke(c)

    def should_migrate(self, document):
        """ Does this document need to be migrated?
            Only migrate if the document contains an element (other than (sub)paragraph) containing a definition
             that is followed by a (sub)paragraph.
        """
        xml = etree.fromstring(document.document_xml)
        return bool(self.needs_migration_xpath(xml))


def pretty_c14n(xml_text):
    """ Canonicalise and pretty-print an XML document. This ensures that attributes are in canonical (alphabetical)
    order.
    """
    # we can't pretty print and canonicalize in one step. So canonicalize, parse the canonical version (which
    # preserves attrib order), then pretty-print
    return etree.tostring(etree.fromstring(etree.canonicalize(xml_text)), pretty_print=True, encoding='unicode')


def diff_table(first, second, fromdesc, todesc):
    first = first.splitlines(keepends=True)
    second = second.splitlines(keepends=True)

    differ = HtmlDiff()
    differ._wrapcolumn = 100
    return differ.make_table(first, second, context=True, numlines=2, fromdesc=fromdesc, todesc=todesc)
