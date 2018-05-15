# -*- coding: utf-8 -*-

import re

from indigo_api.importers.base import Importer
from indigo_api.importers.registry import importers


@importers.register
class ImporterZA(Importer):
    """ Importer for the Polish tradition.
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
        r'^.*[_-]{5}.*$',
    ]), re.MULTILINE)

    def reformat_text(self, text):
        # change weird quotes to normal ones
        text = re.sub(r"‘‘|’’|''", '"', text)

        # boilerplate
        text = self.boilerplate_re1.sub('', text)
        text = self.boilerplate_re2.sub('', text)

        #text = self.unbreak_lines(text)
        text = self.break_lines(text)

        #s = strip_toc(s)

        return text

"""
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

      # Find likely candidates for unnecessarily broken lines
      # and unbreaks them.
      def unbreak_lines(s)
        lines = s.split(/\n/)
        output = []

        # set of regex matcher pairs, one for the prev line, one for the current line
        matchers = [
          [/[a-z0-9]$/, /^\s*[a-z]/],  # line ends with and starst with lowercase
          [/;$/, /^\s*(and|or)/],      # ends with ; then and/or on new line
        ]

        prev = nil
        lines.each_with_index do |line, i|
          if i == 0
            output << line
          else
            prev = output[-1]
            unbreak = false

            for prev_re, curr_re in matchers
              if prev =~ prev_re and line =~ curr_re
                unbreak = true
                break
              end
            end

            if unbreak
              output[-1] = prev + ' ' + line
            else
              output << line
            end
          end
        end

        output.join("\n")
      end

      # Do our best to remove table of contents at the start,
      # it really confuses the grammer.
      def strip_toc(s)
        # first, try to find 'TABLE OF CONTENTS' anywhere within the first 4K of text,
        if toc_start = s[0..4096].match(/TABLE OF CONTENTS/i)

          # grab the first non-blank line after that, it's our end-of-TOC marker
          if eol = s.match(/^(.+?)$/, toc_start.end(0))
            marker = eol[0]

            # search for the first line that is a prefix of marker (or vv), and delete
            # everything in between
            posn = eol.end(0)
            while m = s.match(/^(.+?)$/, posn)
              if marker.start_with?(m[0]) or m[0].start_with?(marker)
                return s[0...toc_start.begin(0)] + s[m.begin(0)..-1]
              end

              posn = m.end(0)
            end
          end
        end

        s
      end
    
"""
