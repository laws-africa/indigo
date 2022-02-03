from django.conf import settings

from .pipeline import Stage, shell
from indigo_api.importers.pdfs import pdf_extract_pages


class PdfExtractPages(Stage):
    """ Extracts specified pages from a PDF file.

    Reads: context.source_file
    """
    def __call__(self, context):
        if context.page_nums:
            pdf_extract_pages(context.source_file.name, context.page_nums, context.source_file.name)


class PdfToText(Stage):
    """ Converts a PDF file into HTML.

    Reads: context.source_file
    Writes: context.text
    """

    def __call__(self, context):
        context.text = self.pdf_to_text(context.source_file.name, context.cropbox)

    def pdf_to_text(self, fname, cropbox):
        cmd = [settings.INDIGO_PDFTOTEXT, "-enc", "UTF-8", "-nopgbrk", "-raw"]

        if cropbox:
            # left, top, width, height
            cropbox = (str(int(float(i))) for i in cropbox)
            cropbox = list(zip("-x -y -W -H".split(), cropbox))
            # flatten
            cmd += [x for pair in cropbox for x in pair]

        cmd += [fname, '-']
        code, stdout, stderr = shell(cmd)

        if code > 0:
            raise ValueError(stderr)

        return stdout.decode('utf-8')
