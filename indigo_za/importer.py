# -*- coding: utf-8 -*-
import re

from indigo_api.importers.base import Importer
from indigo.plugins import plugins


@plugins.register('importer')
class ImporterZA(Importer):
    """ Importer for the South African tradition.
    """
    locale = ('za', None, None)

    slaw_grammar = 'za'

    boilerplate_re1 = re.compile('|'.join([
        # nuke any line to do with Sabinet and the government printer
        r'^.*Sabinet.*Government Printer.*$',
        r'^.*This gazette is also available.*$',
    ]), re.MULTILINE | re.IGNORECASE)

    boilerplate_re2 = re.compile('|'.join([
        r'^.*PROVINCIAL GAZETTE.*$',
        r'^.*PROVINSIALE KOERANT.*$',
        # get rid of date lines
        r'^\d{1,2}\s+\w+\s+\d{4}$',
        # get rid of page number lines
        r'^\s*page \d+( of \d+)?\s*\n',
        r'^\s*\d*\s*No\. \d+$',
        # get rid of lines with lots of ____ or ---- chars, they're usually pagebreaks
        # but not fill-in-the-blanks in forms
        r'^\s*[_-]{5,}\s*$',
    ]), re.MULTILINE)

    def reformat_text(self, text):
        # change weird quotes to normal ones
        text = re.sub(r"‘‘|’’|''", '"', text)

        # boilerplate
        text = self.boilerplate_re1.sub('', text)
        text = self.boilerplate_re2.sub('', text)

        text = self.unbreak_lines(text)
        text = self.break_lines(text)
        text = self.strip_toc(text)

        return text

    def break_lines(self, text):
        """ Make educated guesses about lines that should have been broken but haven't, and break them.
        There are lots of rules of thumb that make this work.
        """

        # often we find a section title munged onto the same line as its first statement
        # eg:
        # foo bar. New section title 62. (1) For the purpose
        text = re.sub(r'\. ([^.]+) (\d+\. ?\(1\) )', '.\n\\1\n\\2', text)

        # New section title 62. (1) For the purpose
        text = re.sub(r'(\w) (\d+\. ?\(1\) )', '\\1\n\\2', text)

        # (1) foo; (2) bar
        # (1) foo. (2) bar
        text = re.sub(r'(\w{3,}[;.]) (\([0-9a-z]+\))', '\\1\n\\2', text)

        # (1) foo; and (2) bar
        # (1) foo; or (2) bar
        text = re.sub(r'; (and|or) \(', '; \\1\n(', text)

        # The officer-in-Charge may – (a) remove all withered natural... \n(b)
        # We do this last, because by now we should have reconised that (b) should already
        # be on a new line.
        text = re.sub(r' (\(a\) .+?\n\(b\))', '\n\\1', text)

        # "foo" means ...; "bar" means
        text = re.sub(r'; (["”“][^"”“]+?["”“] means)', ';\n\\1', text)

        # CHAPTER 4 PARKING METER PARKING GROUNDS Place of parking
        text = re.sub(r'([A-Z0-9 ]{5,}) ([A-Z][a-z ]{5,})', '\\1\n\\2', text)

        return text

    def unbreak_lines(self, text):
        """ Find likely candidates for unnecessarily broken lines and unbreaks them.
        """
        lines = text.split("\n")
        output = []

        # set of regex matcher pairs, one for the prev line, one for the current line
        matchers = [(
            # line ends with and starts with lowercase
            re.compile(r'[a-z0-9]$'),
            re.compile(r'^\s*[a-z]')
        ), (
            # ends with ; then and/or on new line
            re.compile(r';$'),
            re.compile(r'^\s*(and|or)'),
        )]

        prev = None
        for i, line in enumerate(lines):
            if i == 0:
                output.append(line)
            else:
                prev = output[-1]
                unbreak = False

                for prev_re, curr_re in matchers:
                    if prev_re.search(prev) and curr_re.search(line):
                        unbreak = True
                        break

                if unbreak:
                    output[-1] = prev + ' ' + line
                else:
                    output.append(line)

        return '\n'.join(output)

    def strip_toc(self, text):
        """ Do our best to remove table of contents at the start, it really confuses the grammar.

        We do this by finding the first section-like line after the 'Table of Contents' section.
        We then find the first place where that line is repeated, and consider that the start of the document.
        """
        # first, try to find 'TABLE OF CONTENTS' anywhere within the first 4K of text
        toc_start = re.search(r'TABLE OF CONTENTS|arrangement of sections', text[:4096], re.IGNORECASE)
        if toc_start:
            # grab the first section-link line after that, it will be our end-of-TOC marker
            # eg '1. Definitions'
            first_toc_entry = re.search(r'^\s*(((CHAPTER|PART) +[0-9]+)|[0-9]+\. +\w+)', text[toc_start.end():], re.MULTILINE | re.IGNORECASE)

            if first_toc_entry:
                marker = first_toc_entry.group(1).strip()

                # search for the first line that has a prefix of marker (or vv), and delete
                # everything in between
                posn = toc_start.end() + first_toc_entry.end()

                for match in re.finditer(r'^\s*(.+?)$', text[posn:], re.MULTILINE):
                    if marker.startswith(match.group(1)) or match.group(1).strip().startswith(marker):
                        return text[:toc_start.start()] + text[posn + match.start():]

        return text
