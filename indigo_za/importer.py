import re

from indigo_api.importers.base import Importer
from indigo.plugins import plugins
from docpipe.pipeline import Stage, Pipeline


@plugins.register('importer')
class ImporterZA(Importer):
    """ Importer for the South African tradition.
    """
    locale = ('za', None, None)

    def get_pdf_pipeline(self):
        pipeline = super().get_pdf_pipeline()

        # add specific cleanup before the normal pipeline's parse and serialize stages
        for x in [
            text_cleanup,
            RemoveBoilerplate(),
            UnbreakLines(),
            BreakLines(),
            CorrectSubsectionNumSpaces(),
        ]:
            pipeline.stages.insert(-2, x)
        return pipeline

    def get_docx_pipeline(self):
        pipeline = super().get_docx_pipeline()
        pipeline.stages.insert(-2, text_cleanup)
        return pipeline

    def get_html_pipeline(self):
        pipeline = super().get_html_pipeline()
        pipeline.stages.insert(-2, text_cleanup)
        return pipeline

    def get_file_pipeline(self):
        pipeline = super().get_file_pipeline()
        pipeline.stages.insert(-2, text_cleanup)
        return pipeline


class UnbreakLines(Stage):
    """ Find likely candidates for unnecessarily broken lines and unbreak them.

    Reads: context.text
    Writes: context.text
    """
    def __call__(self, context):
        lines = context.text.split("\n")
        output = []

        # set of regex matcher pairs, one for the prev line, one for the current line
        matchers = [(
            # line ends with lowercase, digit, comma, closing parenthesis, or hyphen;
            # and starts with lowercase or uppercase, the number 0, or a year
            re.compile(r'[a-z0-9,\)-]$'),
            re.compile(r'^\s*([a-zA-Z0]|\d{4})')
        )]

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
                    output[-1] = f'{prev} {line}'
                else:
                    output.append(line)

        context.text = '\n'.join(output)


class BreakLines(Stage):
    """ Make educated guesses about lines that should have been broken but haven't, and break them.
    There are lots of rules of thumb that make this work.

    Reads: context.text
    Writes: context.text
    """
    def __call__(self, context):
        # often we find a section title munged onto the same line as its first statement
        # eg:
        # foo bar. New section title 62. (1) For the purpose
        context.text = re.sub(r'\. ([^.]+) (\d+\. ?\(1\) )', '.\n\\1\n\\2', context.text)

        # New section title 62. (1) For the purpose
        context.text = re.sub(r'(\w) (\d+\. ?\(1\) )', '\\1\n\\2', context.text)

        # (1) foo; (2) bar
        # (1) foo. (2) bar
        context.text = re.sub(r'(\w{3,}[;.]) (\([0-9a-z]+\))', '\\1\n\\2', context.text)

        # (1) foo; and (2) bar
        # (1) foo; or (2) bar
        context.text = re.sub(r'; (and|or) \(', '; \\1\n(', context.text)

        # The officer-in-Charge may – (a) remove all withered natural... \n(b)
        # We do this last, because by now we should have reconised that (b) should already
        # be on a new line.
        context.text = re.sub(r' (\(a\) .+?\n\(b\))', '\n\\1', context.text)

        # "foo" means ...; "bar" means
        context.text = re.sub(r'; (["][^"]+?["] means)', ';\n\\1', context.text)

        # CHAPTER 4 PARKING METER PARKING GROUNDS Place of parking
        context.text = re.sub(r'([A-Z0-9 ]{5,}) ([A-Z][a-z ]{5,})', '\\1\n\\2', context.text)


class RemoveBoilerplate(Stage):
    """ Remove common (South African) boiler-plate.

    Reads: context.text
    Writes: context.text
    """
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

    def __call__(self, context):
        context.text = self.boilerplate_re1.sub('', context.text)
        context.text = self.boilerplate_re2.sub('', context.text)


class CorrectSubsectionNumSpaces(Stage):
    """ Change subsection numbers like ( f) to (f)

    Reads: context.text
    Writes: context.text
    """
    def __call__(self, context):
        context.text = re.sub(r'^\(\s+([a-z0-9]+)\s*\)', '(\\1)', context.text, 0, re.MULTILINE)
        context.text = re.sub(r'^\(([a-z0-9]+)\s+\)', '(\\1)', context.text, 0, re.MULTILINE)


class NormaliseQuotes(Stage):
    """ Change weird quotes to double quotes.

    Reads: context.text
    Writes: context.text
    """
    def __call__(self, context):
        context.text = re.sub(r"‘‘|’’|''|“|”|‟", '"', context.text)


class Unhyphenate(Stage):
    """ Change "hyphen- ated" to "hyphenated".

    This happens particularly when importing from HTML with <br> used in the middle,
    which we change to a space.

    Reads: context.text
    Writes: context.text
    """
    def __call__(self, context):
        context.text = re.sub(r'([a-z])- ([a-z])', '\\1\\2', context.text)


class ExpandLigatures(Stage):
    """ Replace ligatures with separate characters, eg. ﬁ -> fi.

    Reads: context.text
    Writes: context.text
    """
    def __call__(self, context):
        context.text = context.text \
            .replace('ﬁ', 'fi') \
            .replace('ﬀ', 'ff') \
            .replace('ﬃ', 'ffi') \
            .replace('ﬄ', 'ffl') \
            .replace('ﬆ', 'st') \
            .replace('ı', 'i')


# commonly used text cleanup stages
text_cleanup = Pipeline([
    NormaliseQuotes(),
    Unhyphenate(),
    ExpandLigatures(),
])
