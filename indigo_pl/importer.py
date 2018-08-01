# -*- coding: utf-8 -*-
import re

from bs4 import BeautifulSoup
from indigo_api.importers.base import Importer
from indigo.plugins import plugins


@plugins.register('importer')
class ImporterPL(Importer):
    """ Importer for the Polish tradition.
    
    Expects the input PDF files to be in the format produced by the Online Legal Database
    (= "Internetowy System Aktów Prawnych" or "ISAP") of the Polish parliament (= "Sejm")
    for unified texts (= "tekst ujednolicony"). 
    
    Unified texts are NOT the official consolidated texts (= "tekst jednolity"), but ISAP 
    produces them much more often, and they are of very good quality, practically the same as 
    consolidated texts.
    
    See http://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20120001512 for an example law 
    with unified text - the PDF next to "Tekst ujednolicony:".
    """
    
    SUPERSCRIPT_START = "^^SUPERSCRIPT^^"
    SUPERSCRIPT_END = "$$SUPERSCRIPT$$"
    
    locale = ('pl', None, None)

    slaw_grammar = 'pl'

    def pdf_to_text(self, f):
        """Override of pdf_to_text from superclass, using "pdftohtml" instead of "pdftotext".
        We need the HTML (XML actually) with positional info to do some special preprocessing,
        such as recognizing superscripts or how much dashes are indented.

        Args:
            f: The input PDF file.
        """
        cmd = ["pdftohtml", "-zoom", "1.35", "-xml", "-stdout", f.name]
        code, stdout, stderr = self.shell(cmd)
        if code > 0:
            raise ValueError(stderr)
        return stdout.decode('utf-8')

    def reformat_text(self, text):
        """Override of reformat_text from superclass. Here we do our special preprocessing on
        XML, then strip XML tags, and return a plain text string which should finally be parsed
        into Akoma Ntoso.
        
        Args:
            text: String containing XML produced by pdf_to_text.

        Returns:
            str: Plain text containing the law.
        """
        xml = BeautifulSoup(text)
        self.remove_header_and_footer(xml)
        self.process_superscripts(xml)
        self.remove_footnotes(xml)
        text = xml.get_text() # Strip XML tags.
        text = self.join_hyphenated_words(text)
        text = self.remove_linebreaks(text)
        return text

    def remove_header_and_footer(self, xml):
        """Modify the passed in XML by removing tags laying outside the area we know to be
        the actual law text. Generally, this will be the ISAP header, and footer containing 
        page numbers.

        Args:
            xml: The XML to operate on, as a list of tags.
        """
        for tag in xml.find_all(self.is_header_or_footer):
            tag.extract()

    def is_header_or_footer(self, tag):
        """Check if the given tag lies on the page at a position known to be in header or footer.

        Args:
            tag: The tag to check.

        Returns:
            bool: True if tag is in header/footer, False otherwise.
        """
        return ((tag.name == "text") and tag.has_attr("top")
            and ((int(tag["top"]) <= 50) or (int(tag["top"]) > 1060)))

    def process_superscripts(self, xml):
        """Modify the passed in XML by searching for tags which represent superscript numbering and
        combining them with neighboring tags in such a way that superscripts are no longer
        indicated by XML positional info (lower font height and lower offset from page top than
        the rest of line), but by special surrounding text (^^SUPERSCRIPT^^ before and
        $$SUPERSCRIPT$$ after).

        Args:
            xml: The XML to operate on, as a list of tags.
        """
        text_nodes = xml.find_all('text')

        superscript_pattern = re.compile("^[a-z0-9]+$")
        # TODO: We may relax the node_plus_two_pattern a bit, particularly removing the requirement
        # of a period at the beginning. When a division number is mentioned from another place,
        # the period is not always there.
        node_plus_two_pattern = re.compile("^\. .*")
        n = len(text_nodes)
        if (n < 3):
            return

        nodes_to_remove = []

        for _ in xrange(0, n - 3):
            node = text_nodes.pop(0)
            node_plus_one = text_nodes[0]
            node_plus_two = text_nodes[1]

            node_txt = node.get_text()
            node_plus_one_txt = node_plus_one.get_text()
            node_plus_two_txt = node_plus_two.get_text()

            if not superscript_pattern.match(node_plus_one_txt):
                continue

            if not node_plus_two_pattern.match(node_plus_two_txt):
                continue

            if ((not node.has_attr("height")) or (not node_plus_one.has_attr("height"))
                    or (not node_plus_two.has_attr("height")) or (not node.has_attr("top"))
                    or (not node_plus_one.has_attr("top")) or (not node_plus_two.has_attr("top"))):
                continue

            # node and node_plus_two must have the same height.
            if int(node["height"]) != int(node_plus_two["height"]):
                continue

            # node_plus_one must have lower height than node/node_plus_two (smaller font).
            if int(node["height"]) <= int(node_plus_one["height"]):
                continue

            # node and node_plus_two must be in same line.
            if int(node["top"]) != int(node_plus_two["top"]):
                continue

            # node_plus_one must not be below the line of node/node_plus_two.
            if int(node["top"]) < int(node_plus_one["top"]):
                continue

            # Concat all three nodes, surrounding text of node_plus_one with special labels.
            # Put concatenated text in node, remove node_plus_one & node_plus_two.
            node.string = (node_txt + self.SUPERSCRIPT_START + node_plus_one_txt
                + self.SUPERSCRIPT_END + node_plus_two_txt)
            nodes_to_remove.append(node_plus_one)
            nodes_to_remove.append(node_plus_two)

        for node in nodes_to_remove:
            node.extract()

    def remove_footnotes(self, xml):
        """Modify the passed in XML by searching for tags which have smaller font ("height"
        attribute) than most tags in the document. Remove all such tags. This definitively
        removes footnotes.

        TODO: Check if we don't remove too much.

        Args:
            xml: The XML to operate on, as a list of tags.
        """
        text_nodes = xml.find_all('text')

        # Find the most commonly occurring height of text nodes. We'll assume this is
        # the height of the law text itself.
        heights = {}
        for node in text_nodes:
            if not node.has_attr("height"):
                continue
            height = int(node["height"])
            heights[height] = ((heights[height] + 1) if heights.has_key(height) else 1)
        most_common_height = max(heights, key = heights.get)

        # Remove all text nodes whose height is lower than most_common_height.
        for node in text_nodes:
            if node.has_attr("height") and (int(node["height"]) < most_common_height):
                node.extract()

    def join_hyphenated_words(self, text):
        """ Join hyphenated words - ones that have been split in middle b/c of line end.

        Args:
            text (str): The law text.

        Returns:
            str: The law text after processing.
        """
        return re.sub(ur"([a-ząćęłńśóźż])-\n([a-ząćęłńśóźż])", "\g<1>\g<2>", text)

    def remove_linebreaks(self, text):
        """ Remove all line breaks, except when the new line starts with a symbol known
        to be the start of a division.

        Args:
            text (str): The law text.

        Returns:
            str: The law text with line breaks removed.
        """
        return re.sub(ur"\n(?!("
                      u"DZIAŁ [IVXLC]|"
                      u"Rozdział [IVXLC1-9]|"
                      u"Art\.|"
                      u"§ \d+[a-z]*\.|"
                      u"\d+[a-z]*\.|"
                      u"\d+[a-z]*\)|"
                      u"[a-z]+\)|"
                      u"–))", " ", text)
