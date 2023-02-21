import re

from docpipe.pipeline import Stage, Pipeline

from indigo.pipelines.base import chomp_left
from indigo.pipelines.hier import IndentBlocks


class MarkPreface(Stage):
    """ Mark everything before the first akn-block as preface.

    Reads: context.html
    Writes: context.html
    """
    def __call__(self, context):
        preface = context.html.makeelement('akn-block', attrib={'name': 'PREFACE'})
        added = False

        for elem in context.html:
            if elem.tag == "akn-block":
                break

            if not added:
                elem.addprevious(preface)
                added = True
            preface.append(elem)


class IdentifySpeech(Stage):
    """ Identify speeches.

    eg.:

       HON. ABDIAZIZ ABDILAHI MOHAMED [SOMALIA]: Thank you for giving me...
       [AN HONOURABLE MEMBER] : ...
       [AN HONOURABLE MEMBER] : 23:33:8 ...

    Reads: context.html
    Writes: context.html
    """

    # anything except a lowercase character
    from_re = re.compile(r'^[^a-z]+:', re.UNICODE)

    def __call__(self, context):
        for p in context.html.xpath('./p'):
            text = ''.join(p.itertext()).strip()
            if ':' not in text:
                continue

            from_ = self.from_re.search(text)
            if from_:
                from_text = from_.group(0)
                # don't break across [ ... ] boundaries
                if '[' in from_text and ']' not in from_text:
                    from_text = from_text[:from_text.index('[') - 1]

                if len(from_text) > 5:
                    block = p.makeelement('akn-block', attrib={'name': 'SPEECH', 'from': from_text})
                    p.addprevious(block)
                    chomp_left(p, len(from_text))


class IdentifyRemarks(Stage):
    """ Identify remarks, which are in parens or brackets, and may be italics.

    eg:
      (Foo)
      [Foo]

    Reads: context.html
    Writes: context.html
    """

    def __call__(self, context):
        for p in context.html.xpath('./p'):
            text = ''.join(p.itertext()).strip()
            kids = list(p)

            # we want either no kids, or all italics
            italics = ''.join(p.xpath('./i//text()'))
            if kids and italics and italics != text:
                continue

            if (
                    (text.startswith('(') and text.endswith(')')) or
                    (text.startswith('[') and text.endswith(']'))
            ):
                # mark the entire line as a remark
                remark = p.makeelement('akn-inline', attrib={'marker': '*'})
                remark.text = text
                for kid in kids:
                    p.remove(kid)
                p.text = ''
                p.append(remark)


class WrapDebate(Stage):
    """ Wrap everything after the preface in a single debate block.

    Reads: context.html
    Writes: context.html
    """
    def __call__(self, context):
        kids = list(context.html)
        if not kids:
            return

        if kids[0].tag == 'akn-block' and kids[0].attrib['name'] == 'PREFACE':
            kids.pop(0)

        debateSection = context.html.makeelement("akn-block", attrib={'name': 'DEBATESECTION'})
        for kid in kids:
            debateSection.append(kid)

        body = context.html.makeelement("akn-block", attrib={'name': 'BODY'})
        body.append(debateSection)
        context.html.append(body)


hierarchicalizeDebate = Pipeline([
    IdentifySpeech(),
    IdentifyRemarks(),

    # do this after identifying everything else, so we can stop the moment we find an akn-block
    MarkPreface(),

    # TODO: [FRENCH] or whatever as an editorial remark
    # TODO: (applause) as remarks
    # TODO: adjournment?
    IndentBlocks(),

    # everything after the preface must go into BODY > DEBATESECTION
    WrapDebate(),
], name="Hierarchicalize debate")
