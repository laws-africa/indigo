import re
import logging
from collections import Counter
from itertools import chain
from lxml import etree

from indigo.plugins import LocaleBasedMatcher
from schemas import AkomaNtoso30

log = logging.getLogger(__name__)


class BaseTermsFinder(LocaleBasedMatcher):
    """ Finds references to defined terms in documents.

    Subclasses must implement `find_terms_in_document`.
    """

    heading_re = None  # subclasses must define this
    term_re = None     # subclasses must define this, the matched term must be in a (group)
    non_alphanum_re = re.compile(r'\W', re.UNICODE)

    # elements with headings to look for definitions in
    defn_hier = AkomaNtoso30.hier_elements
    # elements on which to attach the main refersTo for the definition
    ancestors = defn_hier + ['item', 'p', 'blockList']
    # elements which must not be checked for references to terms
    no_term_markup = ['term', 'ref', 'remark']

    ontology_template = "/ontology/term/this.{language}.{term}"

    @property
    def language(self):
        return self.locale[1]

    def find_terms_in_document(self, document):
        """ Find defined terms in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content)
        self.find_terms(root)
        document.content = etree.tostring(root, encoding='utf-8').decode('utf-8')

    def find_terms(self, doc):
        self.setup(doc)

        self.guess_at_definitions(doc)
        terms = self.find_definitions(doc)
        self.add_terms_to_references(doc, terms)
        self.find_term_references(doc, terms)
        self.renumber_terms(doc)

    def setup(self, doc):
        self.ns = doc.nsmap[None]
        self.nsmap = {'a': self.ns}

        self.ancestors = ['{%s}%s' % (self.ns, x) for x in self.ancestors]
        self.def_tag = '{%s}def' % self.ns
        self.term_tag = '{%s}term' % self.ns
        self.tlc_term_tag = "{%s}TLCTerm" % self.ns
        self.ref_tag = '{%s}ref' % self.ns
        self.no_term_markup = ['{%s}%s' % (self.ns, x) for x in self.no_term_markup]

        self.defn_hier_xpath = etree.XPath(
            '|'.join(f'//a:{x}' for x in self.defn_hier),
            namespaces=self.nsmap)
        self.heading_xpath = etree.XPath('a:heading', namespaces=self.nsmap)
        self.defn_containers_xpath = etree.XPath('.//a:p|.//a:listIntroduction', namespaces=self.nsmap)
        self.text_xpath = etree.XPath('//a:body//text()', namespaces=self.nsmap)

    def find_definitions(self, doc):
        """ Find `def` elements in the document and return a dict from term ids to the text of the term.
        """
        terms = {}
        for defn in doc.xpath('//a:def', namespaces=self.nsmap):
            # <p>"<def refersTo="#term-affected_land">affected land</def>" means land in respect of which an application has been lodged in terms of section 17(1);</p>

            id = defn.get('refersTo')
            if id and defn.text:
                # strip starting hash
                id = id[1:]
                terms[id] = defn.text

        return terms

    def guess_at_definitions(self, doc):
        """ Find defined terms in the document, such as:

          "this word" means something...

        It identifies "this word" as a defined term and wraps it in a def tag with a refersTo
        attribute referencing the term being defined. The surrounding block
        structure is also has its refersTo attribute set to the term. This way, the term
        is both marked as defined, and the container element with the full
        definition of the term is identified.
        """
        for section in self.definition_sections(doc):
            # find items like "foo" means blah...
            for container in self.defn_containers_xpath(section):
                # only if we don't already have a definition here
                if list(container.iterchildren(self.def_tag)):
                    continue

                if not container.text:
                    continue

                match = self.term_re.search(container.text)
                if match:
                    # the term is in group(1) or higher: skip all `None`s
                    n = 0
                    m = None
                    while not m:
                        n += 1
                        m = match.group(n)
                    self.mark_definition(container, match.group(n), match.start(n), match.end(n))

    def mark_definition(self, container, term, start_pos, end_pos):
        """ Update the container node to wrap the given term in a definition tag.
        """
        term_id = 'term-' + self.non_alphanum_re.sub('_', term)

        # <p>"<def refersTo="#term-affected_land">affected land</def>" means land in respect of which an application has been lodged in terms of section 17(1);</p>
        defn = etree.Element(self.def_tag)
        defn.text = container.text[start_pos:end_pos]
        defn.set('refersTo', '#' + term_id)
        # trailing text
        defn.tail = container.text[end_pos:]

        # before definition
        container.text = container.text[0:start_pos]

        # definition
        container.insert(0, defn)

        # adjust the closest best ancestor's refersTo attribute
        for parent in chain([container], container.iterancestors(self.ancestors)):
            if parent.tag in self.ancestors:
                parent.set('refersTo', '#' + term_id)
                break

    def definition_sections(self, doc):
        """ Yield sections (or other basic units) that potentially contain definitions of terms.
        """
        for section in self.defn_hier_xpath(doc):
            # sections with headings like Definitions
            heading = self.heading_xpath(section)
            if not heading or not self.heading_re.match(heading[0].text or ''):
                continue

            yield section

    def add_terms_to_references(self, doc, terms):
        """ Add defined terms to the references section of the XML.
        """
        refs = doc.xpath('//a:meta/a:references', namespaces=self.nsmap)
        if not refs:
            refs = etree.Element("{%s}references" % self.ns)
            refs.set('source', '#this')
            doc.xpath('//a:meta/a:identification', namespaces=self.nsmap)[0].addnext(refs)
        else:
            refs = refs[0]

        # nuke all existing term reference elements
        for ref in refs.iterchildren(self.tlc_term_tag):
            ref.getparent().remove(ref)

        for id, term in terms.items():
            self.build_tlc_term(refs, id, term)

    def build_tlc_term(self, parent, id, term):
        """ Build an element such as <TLCTerm eId="term-applicant" href="/ontology/term/this.eng.applicant" showAs="Applicant"/>
        """
        elem = etree.SubElement(parent, self.tlc_term_tag)
        elem.set('eId', id)
        elem.set('showAs', term)
        ref = id
        if ref.startswith('term-'):
            ref = ref[5:]
        elem.set('href', self.ontology_template.format(language=self.language, term=ref))

    def find_term_references(self, doc, terms):
        """ Find and decorate references to terms in the document.
        The +terms+ param is a dict from term_id to actual term.
        """
        if not terms:
            return

        # term to term id
        term_lookup = self.make_term_index(terms)

        # big regex of all the terms, longest first
        terms = sorted(term_lookup.keys(), key=lambda t: -len(t))
        terms_re = re.compile(r'\b(%s)\b' % '|'.join(re.escape(t) for t in terms))

        def make_term(match):
            term_id = term_lookup[match.group(1)]
            term = etree.Element(self.term_tag)
            term.text = match.group()
            term.set('refersTo', '#' + term_id)
            return term

        def in_own_defn(node, match):
            # don't link to a term inside its own definition
            term_id = '#' + term_lookup[match.group(1)]
            for ancestor in node.iterancestors(self.ancestors):
                if ancestor.get('refersTo'):
                    return ancestor.get('refersTo') == term_id

        for candidate in self.text_xpath(doc):
            node = candidate.getparent()

            # skip if we're already inside a def or term element
            if node.tag in self.no_term_markup or len(list(node.iterancestors(self.no_term_markup))) > 0:
                continue

            if not candidate.is_tail:
                # text directly inside a node
                for match in terms_re.finditer(node.text):
                    log.debug("Matched " + match.group(1))
                    if in_own_defn(node, match):
                        log.debug("In own definition")
                        continue

                    term = make_term(match)
                    node.text = match.string[:match.start()]
                    node.insert(0, term)
                    term.tail = match.string[match.end():]

                    # now continue to check the new tail
                    node = term
                    break

            while node is not None and node.tail:
                for match in terms_re.finditer(node.tail):
                    log.debug("Matched " + match.group(1))
                    if in_own_defn(node, match):
                        log.debug("In own definition")
                        continue

                    term = make_term(match)
                    node.addnext(term)
                    node.tail = match.string[:match.start()]
                    term.tail = match.string[match.end():]

                    # now continue to check the new tail
                    node = term
                    break
                else:
                    break

    def make_term_index(self, terms):
        return {v: k for k, v in terms.items()}

    def renumber_terms(self, doc):
        """ Recalculate eIds for <term> elements
        """

        def get_parent_id(node):
            parent = node.getparent()
            parent_id = parent.get("eId")
            return parent_id if parent_id else get_parent_id(parent)

        # generate correct term ids, based on the parent id
        counter = Counter()
        for node in doc.xpath('//a:term', namespaces=self.nsmap):
            prefix = get_parent_id(node)
            # the num for this term depends on the number of preceding terms with the same prefix
            counter[prefix] += 1
            node.set('eId', f'{prefix}__term_{counter[prefix]}')
