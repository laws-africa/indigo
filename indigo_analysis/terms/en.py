# -*- coding: utf-8 -*-

import re
from lxml import etree

from indigo_analysis.terms.base import BaseTermsFinder


class TermsFinderEN(BaseTermsFinder):
    """ Finds references to defined terms in documents.
    """

    # country, language, locality
    locale = (None, 'eng', None)

    def find_terms_in_document(self, document):
        """ Find defined terms in +document+, which is an Indigo Document object.
        """
        # we need to use etree, not objectify, so we can't use document.doc.root,
        # we have to re-parse it
        root = etree.fromstring(document.content)
        self.find_terms(root)
        document.content = etree.tostring(root, encoding='UTF-8')

    def find_terms(self, doc):
        self.ns = doc.nsmap[None]
        self.nsmap = {'a': self.ns}

        terms = self.find_definitions(doc)
        self.add_terms_to_references(doc, terms)
        self.find_term_references(doc, terms)
        self.renumber_terms(doc)

    def find_definitions(self, doc):
        """ Find `def` elements in the document and return a dict from term ids to the text of the term.
        """
        #self.guess_at_definitions(doc)

        terms = {}
        for defn in doc.xpath('//a:def', namespaces=self.nsmap):
            # <p>"<def refersTo="#term-affected_land">affected land</def>" means land in respect of which an application has been lodged in terms of section 17(1);</p>

            id = defn.get('refersTo')
            if id:
                # strip starting hash
                id = id[1:]
                terms[id] = defn.text

        return terms

    def add_terms_to_references(self, doc, terms):
        refs = doc.xpath('//a:meta/a:references', namespaces=self.nsmap)
        if refs is None:
            refs = etree.Element("{%s}references" % self.ns)
            refs.set('source', '#this')
            doc.xpath('//a:meta/a:identification', namespaces=self.nsmap)[0].addnext(refs)
        else:
            refs = refs[0]

        # nuke all existing term reference elements
        for ref in refs.xpath('a:TLCTerm', namespaces=self.nsmap):
            ref.getparent().remove(ref)

        for id, term in terms.iteritems():
            # <TLCTerm id="term-applicant" href="/ontology/term/this.eng.applicant" showAs="Applicant"/>
            elem = etree.SubElement(refs, "{%s}TLCTerm" % self.ns)
            elem.set('id', id)
            elem.set('showAs', term)
            ref = id
            if ref.startswith('term-'):
                ref = ref[5:]
            elem.set('href', "/ontology/term/this.eng." + ref)

    def guess_at_definitions(self, doc):
        """ Find defined terms in the document.

        This looks for heading elements with the words 'definitions' or 'interpretation',
        and then looks for phrases like

          "this word" means something...

        It identifies "this word" as a defined term and wraps it in a def tag with a refersTo
        attribute referencing the term being defined. The surrounding block
        structure is also has its refersTo attribute set to the term. This way, the term
        is both marked as defined, and the container element with the full
        definition of the term is identified.
        """

        # TODO
        """

        doc.xpath('//a:section', a: NS).select do |section|
          # sections with headings like Definitions
          heading = section.at_xpath('a:heading', a: NS)
          heading && heading.content =~ /definition|interpretation/i
        end.each do |section|
          # find items like "foo" means blah...
          
          section.xpath('.//a:p|.//a:listIntroduction', a: NS).each do |container|
            # only if we don't already have a definition here
            next if container.at_xpath('a:def', a: NS)

            # get first text node
            text = container.children.first
            next if (not text or not text.text?)

            match = /^\s*["“”](.+?)["“”]/.match(text.text)
            if match
              term = match.captures[0]
              term_id = 'term-' + term.gsub(/[^a-zA-Z0-9_-]/, '_')

              # <p>"<def refersTo="#term-affected_land">affected land</def>" means land in respect of which an application has been lodged in terms of section 17(1);</p>
              refersTo = "##{term_id}"
              defn = doc.create_element('def', term, refersTo: refersTo)
              rest = match.post_match

              text.before(defn)
              defn.before(doc.create_text_node('"'))
              text.content = '"' + rest

              # adjust the container's refersTo attribute
              parent = find_up(container, ['item', 'point', 'blockList', 'list', 'paragraph', 'subsection', 'section', 'chapter', 'part'])
              parent['refersTo'] = refersTo
            end
          end
        end
      end

    # Find and decorate references to terms in the document.
    # The +terms+ param is a hash from term_id to actual term.
    def find_term_references(doc, terms)
      logger.info("+ Finding references to terms")

      i = 0

      # sort terms by the length of the defined term, desc,
      # so that we don't find short terms inside longer
      # terms
      terms = terms.to_a.sort_by { |pair| -pair[1].size }

      # look for each term
      for term_id, term in terms
        doc.xpath('//a:body//text()', a: NS).each do |text|
          # replace all occurrences in this text node

          # unless we're already inside a def or term element
          next if (["def", "term"].include?(text.parent.name))

          # don't link to a term inside its own definition
          owner = find_up(text, 'subsection')
          next if owner and owner.at_xpath(".//a:def[@refersTo='##{term_id}']", a: NS)

          while posn = (text.content =~ /\b#{Regexp::escape(term)}\b/)
            # <p>A delegation under subsection (1) shall not prevent the <term refersTo="#term-Minister" id="trm357">Minister</term> from exercising the power himself or herself.</p>
            node = doc.create_element('term', term, refersTo: "##{term_id}", id: "trm#{i}")

            pre = (posn > 0) ? text.content[0..posn-1] : nil
            post = text.content[posn+term.length..-1]

            text.before(node)
            node.before(doc.create_text_node(pre)) if pre
            text.content = post

            i += 1
          end
        end
      end
    end

    # recalculate ids for <term> elements
    def renumber_terms(doc)
      logger.info("Renumbering terms")

      doc.xpath('//a:term', a: NS).each_with_index do |term, i|
        term['id'] = "trm#{i}"
      end
    end

"""
