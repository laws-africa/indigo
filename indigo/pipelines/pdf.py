from docpipe.pipeline import Stage
from indigo_api.importers.pdfs import pdf_extract_pages


class PdfExtractPages(Stage):
    """ Extracts specified pages from a PDF file.

    Reads: context.source_file
    """
    def __call__(self, context):
        if context.page_nums:
            pdf_extract_pages(context.source_file.name, context.page_nums, context.source_file.name)
