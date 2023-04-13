from django.utils.translation import gettext as _

from docpipe.pipeline import Stage


class ImportSourceFile(Stage):
    """ Import the source file as text.

    Reads: context.source_file
    Writes: context.text or context.html_text, depending on constructor
    """
    def __init__(self, attr='text'):
        self.attr = attr

    def __call__(self, context):
        setattr(context, self.attr, context.source_file.read().decode('utf-8'))


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
