import re

from docpipe.pipeline import Stage, Pipeline
from indigo.pipelines.base import chomp_left, is_centered


class IdentifySections(Stage):
    """ Identifies and marks sections blocks. This should be done after more obvious blocks have been identified,
    because it doesn't guard against mistaking, say, "Part A - Foo" as a heading if it preceeds a section without
    an inline heading.

    These are of the form:

        1 heading
        1a. heading

    There is a chance that these are actually numbered paragraphs. The primary differentiator is that numbered
    paragraphs don't have headings.

    Reads: context.html
    Writes: context.html
    """

    # 1 foo
    # 1a foo
    title_re = re.compile(r"^(\d+[a-zA-Z]{0,2}\.?)(\s+)(.+)$")

    # if it's longer than this, it's probably not a heading
    max_heading_length = 80

    def __call__(self, context):
        for p in context.html.xpath('./p'):
            # lstrip text in case there's inline whitespace at the start
            text = ''.join(p.xpath('.//text()')).lstrip()
            if text:
                m = self.title_re.match(text)
                if m:
                    # everything after the number, which could be a heading, plain text, or a subparagraph number
                    rest = m.group(3).strip()

                    # does it look like a subsection, eg: 2. (1) Lorem ipsum
                    has_subsec = IdentifySubsections.num_re.match(rest)

                    # is "rest" a heading?
                    rest_is_heading = not has_subsec and self.is_heading_text(p, rest)

                    # is there a heading on the previous line?
                    heading = None
                    if not rest_is_heading:
                        prev_p = p.getprevious()
                        if prev_p is not None and prev_p.tag == "p":
                            text = ''.join(prev_p.xpath('.//text()'))
                            if self.is_heading_text(prev_p, text) or is_centered(prev_p):
                                # looks like a heading, we'll use it
                                heading = text
                                prev_p.getparent().remove(prev_p)

                    # it's a section (and not a numbered paragraph) if:
                    #  1. it has a subsection inside it, or
                    #  2. it has a heading, or
                    #  3. it doesn't have a heading, but it does have some small amount of text
                    if has_subsec or rest_is_heading or (text and len(rest) < self.max_heading_length) or heading:
                        block = p.makeelement('akn-block', attrib={
                            "name": "SECTION",
                            "num": m.group(1)
                        })
                        p.addprevious(block)

                        if heading:
                            block.attrib["heading"], block.attrib["stop_stripped"] = self.clean_heading(heading)

                        if rest_is_heading:
                            # it has a heading, we consume the entire element
                            # TODO: this means we can't have rich HTML headings
                            block.attrib["heading"], block.attrib["stop_stripped"] = self.clean_heading(rest)
                            p.getparent().remove(p)

                        else:
                            # no heading, consume the number and the whitespace
                            chomp_left(p, m.span(2)[1])

    def is_heading_text(self, elem, text):
        text = text.strip()
        if elem.tag != 'p' or not text:
            return False

        # eg. "In this Act-"
        if text[-1] in ['-', '—', ';', ':']:
            return False

        bold = ''.join(elem.xpath('.//b//text()'))
        return len(text) <= self.max_heading_length or text in bold

    def clean_heading(self, text):
        cleaned = text.rstrip('.')
        return cleaned, 'true' if cleaned != text else 'false'


class IdentifySectionHeadings(IdentifySections):
    """ Look for headings that come before sections.

    Reads: context.html
    Writes: context.html
    """

    def __call__(self, context):
        for block in context.html.xpath('.//akn-block[@name="SECTION" and not(@heading)]'):
            p = block.getprevious()
            if p is not None and p.tag == "p":
                text = ''.join(p.xpath('.//text()'))
                if self.is_heading_text(p, text) or is_centered(p):
                    # looks like a heading
                    block.attrib['heading'], block.attrib['stop_stripped'] = self.clean_heading(text)
                    p.getparent().remove(p)


class IdentifySubsections(Stage):
    """ Identifies and marks subsections.
    Reads: context.html
    Writes: context.html
    """

    # (1)
    # (1a)
    num_re = re.compile(r"^(\(\d+[a-zA-Z]{0,2}\))\s+")
    block_name = "SUBSECTION"

    def __call__(self, context):
        for p in context.html.xpath('./p'):
            # lstrip text in case there's inline whitespace at the start
            text = ''.join(p.xpath('.//text()')).lstrip()
            if text:
                m = self.num_re.match(text)
                if m:
                    block = p.makeelement("akn-block", attrib={
                        "name": self.block_name,
                        "num": m.group(1),
                    })
                    p.addprevious(block)
                    # now consume everything we've pulled into "num"
                    chomp_left(p, m.span()[1])


class IdentifyParagraphs(IdentifySubsections):
    """ Identifies and marks paragraphs.

        (a) text

    Reads: context.html
    Writes: context.html
    """

    # (1)
    num_re = re.compile(r"^("
                        # (1)
                        r"\([a-zA-Z]{1,4}\)"
                        # 1.1
                        # 1.1a.1
                        r"|(\d{1,3}[a-zA-Z]{0,2}(\.\d{1,3}[a-zA-Z]{0,2})*\.?)"
                        r")\s+")
    block_name = "PARAGRAPH"


class IdentifyNumberedParagraphs(IdentifyParagraphs):
    """ Identifies and numbered paragraphs. This must be done after identifying numbered sections (which look similar).

    These are of the form:

        1 paragraph text
        1a. paragraph text

    Reads: context.html
    Writes: context.html
    """

    # 1 foo
    # 1a foo
    num_re = re.compile(r"^(\d+[a-zA-Z]{0,2}\.?)\s+")


class IdentifyNumberedParagraphsAgain(Stage):
    """ Identifies numbered sections that should be paragraphs.

    These are of the form:

        <akn-block name="SECTION"><num>1</num><heading>paragraph text</heading></akn-block>
        <akn-block name="SECTION"><num>1a.</num><heading>paragraph text</heading></akn-block>

    Reads: context.html
    Writes: context.html
    """
    target_name = 'SECTION'

    def __call__(self, context):
        for block in context.html.xpath(f'.//akn-block[@name="{self.target_name}" and (@heading)]'):
            if self.has_no_content(block):
                self.adjust_block(block)

    def has_no_content(self, elem):
        next_block = elem.getnext()
        return next_block is None or next_block.tag == 'akn-block' and next_block.get('name', '') == self.target_name

    def adjust_block(self, elem):
        # this section has no content; make it a paragraph instead
        elem.attrib['name'] = 'PARAGRAPH'
        # and move its heading into a p
        self.move_heading_into_p(elem)

    def move_heading_into_p(self, elem):
        body_text = elem.get('heading')
        if elem.get('stop_stripped', 'false') == 'true':
            body_text += '.'
        p = elem.makeelement('p')
        p.text = body_text
        elem.append(p)
        del elem.attrib['heading']


class AdjustParagraphHeadings(IdentifyNumberedParagraphsAgain):
    """ Looks for akn-blocks named 'paragraph' that have a heading and don't have any children,
        and moves their heading text into a p.

    Reads: context.html
    Writes: context.html
    """
    target_name = 'PARAGRAPH'

    def has_no_content(self, elem):
        return not bool(elem.getchildren())

    def adjust_block(self, elem):
        self.move_heading_into_p(elem)


class IdentifyParts(Stage):
    """ Identifies and marks parts, which may cross two lines.

        Part 1 - Heading
        Part 1 Heading

        Part 1
        Heading

    Reads: context.html
    Writes: context.html
    """

    # Part 1
    # Part I
    # Part 1: heading
    # Part 1 - heading
    # Part 1—Heading
    # Part 1
    # Heading
    header_re = None
    # the keyword will vary across subclasses
    header_re_keyword = 'Part'
    # the base (num, separator, heading) isn't expected to vary across subclasses
    header_re_base = "\s+(?P<num>[a-z0-9]{1,5})(\s*[:–—-]\s*|\s+)?(?P<heading>.+)?"
    block_name = "PART"

    def __call__(self, context):
        self.set_header_re()
        for p in context.html.xpath('./p'):
            # lstrip text in case there's inline whitespace at the start
            text = ''.join(p.itertext()).lstrip()
            if text:
                m = self.header_re.match(text)
                if m:
                    attrib = {
                        "name": self.block_name,
                        "num": m.group("num"),
                    }

                    # is there a heading?
                    heading = (m.group("heading") or '').strip()
                    if heading:
                        attrib["heading"] = self.clean_heading(heading)
                    else:
                        nxt = p.getnext()
                        # TODO: they could also both be bold
                        if nxt is not None and is_centered(p) and is_centered(nxt):
                            # assume nxt is the heading
                            attrib["heading"] = self.clean_heading(''.join(nxt.xpath('.//text()')))
                            nxt.getparent().remove(nxt)

                    block = p.makeelement("akn-block", attrib=attrib)
                    p.addprevious(block)
                    # remove the node
                    p.getparent().remove(p)

    def set_header_re(self):
        self.header_re = re.compile(rf"^{self.header_re_keyword}{self.header_re_base}$", re.IGNORECASE)

    def clean_heading(self, heading):
        return heading.lstrip('-').rstrip('.')


class IdentifySubparts(IdentifyParts):
    """ Identifies and marks subparts, which may cross two lines.

        Sub-part 1 - Heading
        Subpart 1 Heading

        Subpart 1
        Heading

    Reads: context.html
    Writes: context.html
    """

    # TODO: Subparts rarely have a keyword
    header_re_keyword = 'Sub-?part'
    block_name = "SUBPART"


class IdentifyArticles(IdentifyParts):
    """ Identifies articles.

        Article 1 - heading
        Article 1

    Reads: context.html
    Writes: context.html
    """

    header_re_keyword = 'Article'
    block_name = "ARTICLE"


class IdentifyChapters(IdentifyParts):
    """ Identifies and marks chapters, which may cross two lines.

        Chapter 1 - Heading
        Chapter 1 Heading

        Chapter 1
        Heading

    Reads: context.html
    Writes: context.html
    """

    header_re_keyword = 'Chapter'
    block_name = "CHAPTER"


class IdentifySchedules(Stage):
    """ Identifies and marks schedules.

        Schedule Heading
        Schedule 1 - Heading
        First Schedule - Heading

    Reads: context.html
    Writes: context.html
    """

    header_re = None
    # the keyword will vary across subclasses
    header_re_keyword = 'Schedule'
    block_name = "SCHEDULE"

    def __call__(self, context):
        self.set_header_re()
        for p in context.html.xpath('./p'):
            # lstrip text in case there's inline whitespace at the start
            text = ''.join(p.itertext()).lstrip()
            if text:
                m = self.header_re.match(text)
                if m:
                    attrib = {
                        "name": self.block_name,
                        "heading": text,
                    }

                    block = p.makeelement("akn-block", attrib=attrib)
                    p.addprevious(block)
                    # remove the node
                    p.getparent().remove(p)

    def set_header_re(self):
        self.header_re = re.compile(rf"^((\w+\s+)?{self.header_re_keyword}\b)(.*)?", re.IGNORECASE)


class IdentifyAnnexes(IdentifySchedules):
    header_re_keyword = 'Annex(?:ure)?'
    block_name = "ANNEXURE"


class IdentifyAppendixes(IdentifySchedules):
    header_re_keyword = 'Appendix'
    block_name = "APPENDIX"


class IdentifyAttachments(IdentifySchedules):
    header_re_keyword = 'Attachment'
    block_name = "ATTACHMENT"


class IdentifyAttachmentSubheadings(Stage):
    """ Identify subheadings in all attachments.
        If we have:
            <akn-block name="SCHEDULE">
            <p>
            <akn-block name="PART">
            <p>
        assume that the first <p> after the start of the Schedule is its subheading.
        Do check first that the <p> isn't the only content in the given attachment.

    Reads: context.html
    Writes: context.html
    """
    attachment_keywords = ['ANNEXURE', 'APPENDIX', 'ATTACHMENT', 'SCHEDULE']

    def __call__(self, context):
        name_options = ' or '.join(f'@name="{x}"' for x in self.attachment_keywords)
        for block in context.html.xpath(f'./akn-block[{name_options} and not(@subheading)]'):
            first_el = block.getnext()
            next_el = first_el.getnext()
            if first_el is not None and first_el.tag == 'p' and not self.is_attachment_or_none(next_el):
                block.attrib['subheading'] = ''.join(first_el.itertext())
                first_el.getparent().remove(first_el)

    def is_attachment_or_none(self, elem):
        return elem is None or elem.tag == 'akn-block' and elem.attrib['name'] in self.attachment_keywords


class RenameSectionsInAttachments(Stage):
    """ Looks for any akn-blocks named 'section' or 'subsection' that follow an akn-block with an attachment name,
        and turns them into numbered paragraphs.

    Reads: context.html
    Writes: context.html
    """
    attachment_keywords = ['ANNEXURE', 'APPENDIX', 'ATTACHMENT', 'SCHEDULE']
    section_keywords = ['SECTION', 'SUBSECTION']

    def __call__(self, context):
        in_attachment = False

        for elem in context.html:
            if in_attachment:
                # we're past the first attachment; any sections from here should be paragraphs instead.
                if elem.tag == 'akn-block' and elem.attrib.get('name') in self.section_keywords:
                    elem.attrib['name'] = 'PARAGRAPH'
            elif elem.tag == 'akn-block' and elem.attrib.get('name') in self.attachment_keywords:
                in_attachment = True


class IndentBlocks(Stage):
    """ Indents content between blocks.

    At this point we have:

        <p>...
        <p>...
        <akn-block>...
        <p>...
        <p>...
        <akn-block>...
        <p>...
        <p>...

    This pushes content between blocks into the preceding block:

        <p>...
        <p>...
        <akn-block>...
            <p>...
            <p>...
        <akn-block>...
            <p>...
            <p>...

    Reads: context.html
    Writes: context.html
    """

    def __call__(self, context):
        prev_block = None

        for elem in context.html:
            if elem.tag == "akn-block":
                prev_block = elem

            elif prev_block is not None:
                # indent it
                prev_block.append(elem)


class IdentifyBody(Stage):
    """ Inserts body, before the first akn-block.

    Reads: context.html
    Writes: context.html
    """

    marker = "BODY"

    def __call__(self, context):
        for elem in context.html:
            if elem.tag == "akn-block":
                body = elem.makeelement('akn-block', attrib={"name": self.marker})
                elem.addprevious(body)
                break


class IdentifyPreamble(Stage):
    """ Identifies preambles, stopping at the first akn-block.

    Reads: context.html
    Writes: context.html
    """

    marker = "PREAMBLE"

    def __call__(self, context):
        for elem in context.html:
            if self.start_of_pre_block(elem):
                pre_block = elem.makeelement('akn-block', attrib={"name": self.marker})
                elem.addprevious(pre_block)
                break
            elif elem.tag == "akn-block":
                break

    def start_of_pre_block(self, elem):
        """ The PREAMBLE keyword should be inserted before the first p that reads 'Preamble', as long as it's before the first akn-block in the document.
        """
        if elem.tag == "p":
            text = (''.join(elem.xpath('.//text()')) or '').strip()
            return text.upper() == self.marker
        return False


class IdentifyPreface(IdentifyPreamble):
    """ Identifies the preface, stopping at the first akn-block.

    Reads: context.html
    Writes: context.html
    """

    marker = "PREFACE"

    def start_of_pre_block(self, elem):
        """ The PREFACE keyword should be inserted at the very top, if the document doesn't start with a Preamble or go straight into a chapter.
            In other words, before the first p, ol, or ul – but not before the first akn-block.
        """
        return elem.tag != "akn-block"


class NestBlocks(Stage):
    """ Nests blocks hierarchically.

    Recursively decides whether an akn-block's following sibling should be nested inside it.

    At this point we have:
        <p>...
        <p>...
        <akn-block>...
        <akn-block>...
        <akn-block>...
        <akn-block>...
        <akn-block>...

    This stage nests the blocks:

        <p>...
        <p>...
        <akn-block>...
            <akn-block>...
                <akn-block>...
        <akn-block>...
            <akn-block>...

    Reads: context.html
    Writes: context.html
    """

    # never indent inside these
    never = ["PREFACE", "PREAMBLE"]

    # highest precedence
    high = ["ANNEXURE", "APPENDIX", "ATTACHMENT", "SCHEDULE"]

    # lowest precedence - these follow a fixed ordering. Everything else follows the order of appearance
    lows = ["SUBPART", "ARTICLE", "SECTION", "SUBSECTION", "PARAGRAPH", "SUBPARAGRAPH"]

    def __call__(self, context):
        self.encountered = []
        self.nest(context.html)

    def nest(self, root):
        curr = next(root.iterchildren(), None)

        while curr is not None:
            nxt = curr.getnext()
            if nxt is None:
                # we're done
                self.nest(curr)
                break

            if curr.tag != "akn-block" or curr.attrib["name"] in self.never:
                curr = nxt
                continue

            assert nxt.tag == "akn-block", f'Expected akn-block but got {nxt.tag}'

            next_name = nxt.attrib['name']
            curr_name = curr.attrib['name']

            if next_name not in self.high:
                # for discovery-based precedence, record the first time we encounter a name
                if curr_name not in self.lows and curr_name not in self.encountered:
                    self.encountered.append(curr_name)

                if curr_name != next_name:
                    if next_name in self.lows:
                        if curr_name in self.lows:
                            # both lows, nest based on pre-set order
                            if self.lows.index(next_name) > self.lows.index(curr_name):
                                curr.append(nxt)
                                continue
                        else:
                            # non-low must contain low
                            curr.append(nxt)
                            continue
                    elif curr_name not in self.lows:
                        # two non-lows, which did we encounter first?
                        if next_name in self.encountered and self.encountered.index(next_name) > self.encountered.index(curr_name):
                            curr.append(nxt)
                            continue
                        # nest e.g. Part (not in lows) inside attachments; highs should always be at the top level
                        elif curr_name in self.high:
                            curr.append(nxt)
                            continue

            # we've finished dealing with curr
            self.nest(curr)
            curr = curr.getnext()


class NestParagraphs(Stage):
    """ Nest paragraphs according to their numbering schemes.

    We do this by identifying the numbering format of each paragraph in the list and comparing it with the surrounding
    elements. When the numbering format changes, "indent" the following paragraphs.

    We make sure to handle special cases such as `(i)` coming between `(h)` and `(j)` versus being at the start of
    a `(i), (ii), (iii)` run.

    Example:

        (a)
        (b)
        (i)
        (ii)
        (aa)
        (bb)
        (c)
        (d)

    becomes

        (a)
        (b)
          (i)
          (ii)
            (aa)
            (bb)
        (c)
        (d)

    Reads: context.html
    Writes: context.html
    """
    def __call__(self, context):
        group = []
        for para in context.html.xpath('.//akn-block[@name = "PARAGRAPH"]'):
            # we want to work with these as contiguous groups; so wait until we have found the last of a group
            if not self.is_para(para.getnext()):
                # end of a group
                if group:
                    group.append(para)
                    self.nest_items(group[0], self.guess_number_format(group[0]))
                    group = []
            else:
                group.append(para)

    def is_para(self, item):
        return item is not None and item.tag == "akn-block" and item.attrib.get("name") == "PARAGRAPH"

    def nest_items(self, item, our_number_format, prev=None):
        number_format = our_number_format

        while item is not None:
            # ensure it's a paragraph
            if not self.is_para(item):
                return

            num = item.attrib["num"]
            number_format = self.guess_number_format(item, number_format)
            if not number_format:
                break

            # (aa) after (z) is same numbering type, pretend we've always been this format
            if num == "(aa)" and item.getprevious() is not None and item.getprevious().attrib.get("num") == "(z)":
                our_number_format = number_format

            if number_format == our_number_format:
                nxt = item.getnext()
                # make them consecutive
                if prev is not None:
                    prev.addnext(item)
                prev = item
                item = nxt

            elif number_format < our_number_format:
                # this item is "higher" than our format, return to caller and start again at this item
                return item

            else:
                # new nesting
                nxt = item.getnext()
                prev.append(item)
                # now keep nesting at this new level
                item = self.nest_items(nxt, number_format, item)

    def guess_number_format(self, item, prev_format=None):
        num = item.attrib.get("num")
        if not num:
            return None

        prev = item.getprevious()
        nxt = item.getnext()

        if num == "(i)":
            # Special case to detect difference between:
            #
            # (h) foo
            # (i) bar
            # (j) baz
            #
            # and
            #
            # (h) foo
            #   (i)  bar
            #   (ii) baz
            #
            # (i) is NOT a sublist if:
            #   - there was a previous item (h), and
            #     - there is not a next item, or
            #     - the next item is something other than (ii)
            if prev is not None and prev.attrib.get("num", "").startswith("(h") and (nxt is None or nxt.attrib["num"] != "(ii)"):
                return NumberingFormat.a
            else:
                return NumberingFormat.i

        elif num in ["(u)", "(v)", "(x)"]:
            return prev_format

        elif re.match(r"^\([ivx]+", num):
            return NumberingFormat.i

        elif re.match(r"^\([IVX]+", num):
            return NumberingFormat.I

        elif re.match(r"^\([a-z]{2}", num):
            return NumberingFormat.aa

        elif re.match(r"^\([A-Z]{2}", num):
            return NumberingFormat.AA

        elif re.match(r"^\([a-z]+", num):
            return NumberingFormat.a

        elif re.match(r"^\([A-Z]+", num):
            return NumberingFormat.A

        elif re.match(r"^\d+(\.\d+)+$", num):
            return NumberingFormat('i.i', num.count('.'))

        return NumberingFormat.unknown


class NumberingFormat:
    def __init__(self, typ, ordinal):
        self.typ = typ
        self.ordinal = ordinal

    def __eq__(self, other):
        return self.ordinal == other.ordinal

    def __lt__(self, other):
        return self.ordinal < other.ordinal

    def __str__(self):
        return self.typ


# TODO: it would be better to determine precedence based on the order in which these are encountered in the text
NumberingFormat.a = NumberingFormat("a", 0)
NumberingFormat.i = NumberingFormat("i", 1)
NumberingFormat.A = NumberingFormat("A", 2)
NumberingFormat.I = NumberingFormat("I", 3)
NumberingFormat.aa = NumberingFormat("aa", 4)
NumberingFormat.AA = NumberingFormat("AA", 5)
NumberingFormat.unknown = NumberingFormat("unknown", 99)


class NestedSubparagraphs(Stage):
    """ Change nested paragraphs into subparagraphs.

    Reads: context.html
    Writes: context.html
    """
    def __call__(self, context):
        for para in context.html.xpath('.//akn-block[@name="PARAGRAPH"]//akn-block[@name="PARAGRAPH"]'):
            para.attrib["name"] = "SUBPARAGRAPH"


class DedentWrapups(Stage):
    """ Push trailing <p>s at the end of hier into their parent as a wrapup, if it seems like the right thing to do.

    These are paragraphs that:

    * are the last child (of exactly 2 p) of their containing akn-block
    * their containing akn-block is the last child

    eg:
      SUBSECTION (3)

        Subject to subsection (2), if a consumer ...

        PARAGRAPH (a)

          ordinarily offers to supply such goods or services; or

        PARAGRAPH (b)

          acts in a manner consistent with being knowledgeable about the use or provision of those goods or services;

          XXX this paragraph should be a wrapup of SUBSECTION (3)

      SUBSECTION (4)

    Reads: context.html
    Writes: context.html
    """

    def __call__(self, context):
        for p in context.html.xpath('.//akn-block/p[last()]'):
            # we know p is the last of all the p tags, but there may be non-p tags afterwards
            if p.getnext() is not None:
                continue

            # exactly two siblings
            if len(p.getparent().getchildren()) != 2:
                continue

            # is the parent block the last of its siblings?
            if p.getparent().getnext() is not None:
                continue

            # dedent
            p.getparent().addnext(p)


class ConvertParasToBlocklists(Stage):
    """ Convert paragraphs that should be blocklists. These are when a section has multiple P elements, some of which
    are block lists, instead of having a clear structure where every line is a numbered paragraph. This often happens
    in definition sections.

    There are two steps:

    1. identify akn-block elements whose direct children must be adjusted
    2. adjust the children from paragraphs into blocklists

    The akn-blocks that must be changed:

    1. are paragraphs (akn-block[@name=PARAGRAPH]), and
    2. have either multiple consecutive plain-text P elements, or paragraphs with repeating numbers.
    """

    def __call__(self, context):
        for block in context.html.xpath('.//akn-block[akn-block[@name="PARAGRAPH"]]'):
            if self.should_fix(block):
                self.fix(block)

    def should_fix(self, block):
        # look for three p elements in a row
        for p in block.xpath('./p[preceding-sibling::*[1][self::p] and following-sibling::*[1][self::p]]'):
            return True

        # look for repeated paragraph numbers
        nums = set()
        for block in block.xpath('./akn-block[@name="PARAGRAPH" and @num]'):
            num = block.attrib['num']
            if num:
                if num in nums:
                    return True
                nums.add(num)

    def fix(self, block):
        kids = list(block)
        kid = kids[0] if kids else None
        while kid is not None:
            if kid.tag == 'akn-block' and kid.attrib['name'] == 'PARAGRAPH':
                kid = self.make_items(kid).getnext()
            else:
                kid = kid.getnext()

    def make_items(self, para):
        # make an ITEMS block
        items = para.makeelement('akn-block', name="ITEMS")

        # make the preceding P tag the intro for the ITEMS block
        prev = para.getprevious()
        if prev is not None and prev.tag == 'p':
            items.append(prev)

        # add the new ITEMS block to the tree just before para
        para.addprevious(items)

        # move children and siblings of para into the new ITEMS block until it looks like the block should finish,
        # which is when we encounter the second non-block element (eg. two P tags)
        while para is not None and para.tag == 'akn-block' and para.attrib['name'].endswith('PARAGRAPH'):
            # stash this so that we move onto it next, because we're going to move para into ITEMS
            next_para = para.getnext()

            # move this para into the ITEMS block
            items.append(para)

            # keep children of this paragraph until we find the second non-block content, at which point
            # stop -- the remaining content should be "unindented" by moving it out of the ITEMS block and putting
            # it afterwards, as a sibling
            #
            # For example, we move paragraph (c) and (d) in, but then stop at "Agent of a licensee:
            #
            #   PARAGRAPH (c)
            #
            #     a game of chance such as lotto, keno or Powerball in which persons choose or attempt to forecast, ...
            #
            #   PARAGRAPH (d)
            #
            #     the game known as soccer football pool in which persons choose or attempt to forecast, from ...
            #
            #     "Agent of a licensee" means an agent appointed or approved in accordance with the conditions of ...

            found_non_block = False
            kids = list(para)
            kid = kids[0] if kids else None
            while kid is not None:
                if kid.tag != 'akn-block':
                    if not found_non_block:
                        # first non-block element we've seen
                        found_non_block = True
                    else:
                        # this is the second non-block element, we've reached the end of this ITEMS block
                        # everything from kid onwards must be moved to after the ITEMS block
                        for sibling in reversed(list(kid.itersiblings())):
                            items.addnext(sibling)
                        items.addnext(kid)
                        next_para = None
                        break
                elif kid.attrib['name'].endswith('PARAGRAPH'):
                    # recursively do the same for this (sub)paragraph
                    kid = self.make_items(kid)
                kid = kid.getnext()
            para = next_para

        # rewrite all nested blocks to ITEM
        for b in items.xpath('.//akn-block[@name != "ITEMS"]'):
            b.attrib['name'] = 'ITEM'

        return items


class IdentifyContainerHeadings(Stage):
    """ Looks for <akn-block>s that start with a <p> and have further <akn-block> children.
    If that first <p> looks like a heading, make it the parent block's heading rather than intro text.

    Before:
    <akn-block name="PART" num="III">
      <p>ELECTIONS</p>
      <akn-block name="SECTION" num="26" heading="Appointment of returning and other election officers">
        …
      </akn-block>
    </akn-block>

    After:
    <akn-block name="PART" num="III" heading="ELECTIONS">
      <akn-block name="SECTION" num="26" heading="Appointment of returning and other election officers">
        …
      </akn-block>
    </akn-block>

    Reads: context.html
    Writes: context.html
    """
    containers = ['CHAPTER', 'PART']
    max_heading_length = 60

    def __call__(self, context):
        # target elements are akn-blocks without headings that contain at least one p and one akn-block
        for block in context.html.xpath('.//akn-block[not(@heading) and p and akn-block]'):
            children = block.getchildren()
            first = children[0]
            rest = children[1:]
            # the right shape: a container with a p as the first element and akn-blocks as the rest
            if block.attrib['name'] in self.containers and first.tag == 'p' and all(c.tag == 'akn-block' for c in rest):
                text = ''.join(first.itertext()).strip()
                # the right content: the text doesn't look introductory, and isn't too long to be a heading
                if text and text[-1] not in ['-', '—', ';', ':', '.'] and len(text) <= self.max_heading_length:
                    block.attrib['heading'] = text
                    block.remove(first)


hierarchicalize = Pipeline([
    # these are unambiguous and can be identified up front
    IdentifyArticles(),
    IdentifyParts(),
    IdentifySubparts(),
    IdentifyChapters(),
    # TODO: divisions - in particular, centered text or h1/h2 etc. are likely to be division markers

    # these can be more ambiguous
    IdentifySections(),
    IdentifySubsections(),
    IdentifyParagraphs(),
    IdentifyNumberedParagraphs(),

    IdentifySectionHeadings(),
    IdentifyNumberedParagraphsAgain(),

    # identify attachments after all the other elements in the main body
    IdentifySchedules(),
    IdentifyAnnexes(),
    IdentifyAppendixes(),
    IdentifyAttachments(),
    IdentifyAttachmentSubheadings(),
    RenameSectionsInAttachments(),

    # do these after identifying everything else, so we can stop the moment we find an akn-block, since these must
    # always come before everything else.
    # Do Preamble first because it comes after the Preface (and will be an akn-block by the time it's been recognised).
    IdentifyBody(),
    IdentifyPreamble(),
    IdentifyPreface(),

    IndentBlocks(),
    NestBlocks(),
    NestParagraphs(),
    NestedSubparagraphs(),
    AdjustParagraphHeadings(),

    DedentWrapups(),
    ConvertParasToBlocklists(),

    # identify container headings that were missed previously once the structure is set
    IdentifyContainerHeadings(),
], name="Hierarchicalize")
