import re
import tempfile

from django.utils.translation import gettext as _
from lxml import etree
from cobalt.akn import AkomaNtosoDocument

from .pipeline import Stage, shell


class ImportSourceFile(Stage):
    """ Import the source file as text.

    Reads: context.source_file
    Writes: context.text or context.html_text, depending on constructor
    """
    def __init__(self, attr='text'):
        self.attr = attr

    def __call__(self, context):
        setattr(context, self.attr, context.source_file.read().decode('utf-8'))


class NormaliseWhitespace(Stage):
    """ Strip and normalise whitespace in text.

    Reads: context.text
    Writes: context.text
    """
    def __call__(self, context):
        # replacing non-breaking spaces with normal spaces
        context.text = context.text.replace('\xA0', ' ')

        # Remove leading whitespace at the start of non-blank lines.
        context.text = re.sub(r'^[ \t]+([^ \t])', '\\1', context.text, 0, re.MULTILINE)

        # Remove excessive whitespace inside text
        context.text = re.sub(r'(\S)[ \t]{2,}', '\\1 ', context.text)


class ParseSlawText(Stage):
    """ Parse Slaw text into an XML object tree (not text).

    Reads: context.text
    Writes: context.xml
    """
    slaw_grammar = 'za'

    use_ascii = True
    """ Should we pass --ascii to slaw? This can have significant performance benefits
    for large files. See https://github.com/cjheath/treetop/issues/31
    """

    def __call__(self, context):
        cmd = ['bundle', 'exec', 'slaw', 'parse']

        if context.fragment:
            cmd.extend(['--fragment', context.fragment])
            if context.fragment_id_prefix:
                cmd.extend(['--id-prefix', context.fragment_id_prefix])

        if getattr(context, 'section_number_position', None):
            cmd.extend(['--section-number-position', context.section_number_position])

        cmd.extend(['--grammar', self.slaw_grammar])
        cmd.extend(['--input', 'text'])
        if self.use_ascii:
            cmd.extend(['--ascii'])

        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            f.write(context.text.encode('utf-8'))
            f.flush()
            f.seek(0)
            cmd.append(f.name)
            code, stdout, stderr = shell(cmd)

        if code > 0:
            raise ValueError(stderr.decode('utf-8'))

        if not stdout:
            raise ValueError(_("We couldn't get any useful text out of the file"))

        # clean up encoding string in XML produced by slaw
        doc = AkomaNtosoDocument(stdout.decode('utf-8'))
        context.xml = etree.fromstring(doc.to_xml(encoding='unicode'))


class MinTextRequired(Stage):
    """ Ensures a minimum amount of text has been extracted from the file.

    Reads: context.text
    """
    def __init__(self, length=512):
        self.length = length

    def __call__(self, context):
        if len(context.text) < self.length:
            raise ValueError(
                _("There is not enough text in the document to import. You may need to OCR the file first.")
            )
