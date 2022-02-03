import tempfile
import shutil
import logging
import re

from django.core.files.uploadedfile import UploadedFile
from indigo.plugins import plugins, LocaleBasedMatcher
from indigo.pipelines.pipeline import Pipeline, PipelineContext
import indigo.pipelines.xml as xml
import indigo.pipelines.html as html
import indigo.pipelines.text as text
import indigo.pipelines.pdf as pdf
from indigo_api.serializers import AttachmentSerializer


class ImportContext(PipelineContext):
    """ The context that is passed to import pipeline stages to share information.
    """
    doc = None
    source_file = None
    page_nums = None
    cropbox = None
    frbr_uri = None
    fragment = None
    fragment_id_prefix = None
    section_number_position = None
    attachments = None
    html = None
    html_text = None
    xml = None
    xml_text = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachments = []


class ParseContext(PipelineContext):
    """ The context that is passed to parse stages to share information.
    """
    frbr_uri = None
    fragment = None
    fragment_id_prefix = None
    xml = None
    xml_text = None


pages_re = re.compile(r'(\d+)(\s*-\s*(\d+))?')


def parse_page_nums(pages):
    """ Turn a string such as '5,7,9-11,12' into a list of integers and (start, end) range tuples.

    Raises ValueError if a part of the string isn't well-formed.
    """
    page_nums = []

    parts = [p.strip() for p in pages.strip().split(',')]
    # iterate over non-empty items separated by commas
    for part in (p for p in parts if p):
        match = pages_re.fullmatch(part)
        if not match:
            raise ValueError(f"Invalid page number: {part}")
        if match.group(3):
            # tuple
            page_nums.append(
                (int(match.group(1)),
                 int(match.group(3))))
        else:
            # singelton
            page_nums.append(int(match.group(1)))

    return page_nums


@plugins.register('importer')
class Importer(LocaleBasedMatcher):
    """ Imports documents and parses text into Akoma Ntoso using a pipelines.
    """
    log = logging.getLogger(__name__)

    locale = (None, None, None)
    """ Locale for this analyzer, as a tuple: (country, language, locality). None matches anything."""

    fragment = None
    """ The name of the AKN element that we're importing, or None for a full act. """

    fragment_id_prefix = None
    """ The prefix for all ids generated for this fragment """

    section_number_position = 'before-title'
    """ By default, where do section numbers usually lie in relation to their
    title? One of: ``before-title``, ``after-title`` or ``guess``.
    """

    cropbox = None
    """ Crop box to import within, as [left, top, width, height]
    """

    page_nums = None
    """ Pages to import for document types that support it, or None to import them all.
    
    This can either be a string, such as "1,5,7-11" or it can be a list of integers and (first, last) tuples.
    """

    def __init__(self):
        self.docx_pipeline = self.get_docx_pipeline()
        self.pdf_pipeline = self.get_pdf_pipeline()
        self.html_pipeline = self.get_html_pipeline()
        self.file_pipeline = self.get_file_pipeline()
        self.xml_pipeline = self.get_xml_pipeline()
        self.parse_pipeline = self.get_parse_pipeline()

    def get_docx_pipeline(self):
        return Pipeline([
            html.DocxToHtml(),
            html.NormaliseHtmlTextWhitespace(),
            html.ParseHtml(),
            html.CleanHtml(),
            html.MergeAdjacentInlines(),
            html.RemoveEmptyInlines(),
            html.MergeUl(),
            html.CleanTables(),
            html.StripParaWhitespace(),

            html.HtmlToSlawText(),
            text.ParseSlawText(),
            xml.SerialiseXml(),
        ])

    def get_pdf_pipeline(self):
        return Pipeline([
            pdf.PdfExtractPages(),
            pdf.PdfToText(),
            text.MinTextRequired(),
            text.NormaliseWhitespace(),

            text.ParseSlawText(),
            xml.SerialiseXml(),
        ])

    def get_html_pipeline(self):
        return Pipeline([
            html.HtmlToSlawText(),
            text.NormaliseWhitespace(),

            text.ParseSlawText(),
            xml.SerialiseXml(),
        ])

    def get_file_pipeline(self):
        # basic file pipeline, assume plain text
        return Pipeline([
            text.NormaliseWhitespace(),
            text.ParseSlawText(),

            xml.SerialiseXml(),
        ])

    def get_xml_pipeline(self):
        return Pipeline([
            xml.SerialiseXml()
        ])

    def get_parse_pipeline(self):
        return Pipeline([
            text.ParseSlawText(),
            xml.SerialiseXml()
        ])

    def import_from_upload(self, upload, doc, request):
        """ Import an uploaded document into an Akoma Ntoso XML document.

        The upload is an :class:`django.core.files.uploadedfile.UploadedFile` instance.
        """
        self.log.info("Processing upload: filename='%s', content type=%s" % (upload.name, upload.content_type))

        if upload.content_type in ['text/xml', 'application/xml']:
            self.log.info("Processing upload as an AKN XML file")
            self.import_from_xml(upload, doc)

        elif (upload.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                or upload.name.endswith('.docx')):
            # pre-process docx to HTML and then import html
            self.log.info("Processing upload as a DOCX file")
            self.import_from_docx(upload, doc)

        elif upload.content_type == 'application/pdf':
            self.log.info("Processing upload as a PDF file")
            self.import_from_pdf(upload, doc)

        elif upload.content_type == 'text/html':
            self.log.info("Processing upload as an HTML file")
            self.import_from_html(upload, doc)

        else:
            # just try to process the text
            self.log.info("Processing upload as an unknown file")
            self.import_from_file(upload, doc)

        # TODO: make a pipeline?
        self.analyse_after_import(doc)

    def analyse_after_import(self, doc):
        """ Run analysis after first import.
        """
        finder = plugins.for_document('refs', doc)
        if finder:
            finder.find_references_in_document(doc)

        finder = plugins.for_document('refs-subtypes', doc)
        if finder:
            finder.find_references_in_document(doc)

        finder = plugins.for_document('refs-cap', doc)
        if finder:
            finder.find_references_in_document(doc)

        finder = plugins.for_document('refs-act-names', doc)
        if finder:
            finder.find_references_in_document(doc)

        finder = plugins.for_document('internal-refs', doc)
        if finder:
            finder.find_references_in_document(doc)

        italics_terms_finder = plugins.for_document('italics-terms', doc)
        italics_terms = doc.work.country.italics_terms
        if italics_terms_finder and italics_terms:
            italics_terms_finder.mark_up_italics_in_document(doc, italics_terms)

    def import_from_pdf(self, upload, doc):
        context = ImportContext(pipeline=self.pdf_pipeline)
        context.cropbox = self.cropbox
        context.fragment = self.fragment
        context.fragment_id_prefix = self.fragment_id_prefix
        context.section_number_position = self.section_number_position
        if self.page_nums:
            if isinstance(self.page_nums, str):
                self.page_nums = parse_page_nums(self.page_nums)
            if self.page_nums:
                context.page_nums = self.page_nums

        self.import_upload_with_context(upload, doc, context)

    def import_from_docx(self, upload, doc):
        context = ImportContext(pipeline=self.docx_pipeline)
        self.import_upload_with_context(upload, doc, context)

    def import_from_html(self, upload, doc):
        context = ImportContext(pipeline=self.html_pipeline)
        self.import_upload_with_context(upload, doc, context)

    def import_from_file(self, upload, doc):
        context = ImportContext(pipeline=self.file_pipeline)
        self.import_upload_with_context(upload, doc, context)

    def import_from_xml(self, upload, doc):
        context = ImportContext(pipeline=self.xml_pipeline)
        self.import_upload_with_context(upload, doc, context)

    def import_upload_with_context(self, upload, doc, context):
        """ Apply a pipeline with context to import the uploaded file.
        """
        with self.tempfile_for_upload(upload) as f:
            context.frbr_uri = doc.expression_uri
            context.source_file = f
            context.doc = doc
            # run the pipeline
            context.pipeline(context)
            # save the xml
            doc.reset_xml(context.xml_text, from_model=True)
            # save attachments
            self.stash_imported_attachments(context, doc)
            # save the original upload
            self.stash_upload(upload, f, doc)

    def parse_from_text(self, text, frbr_uri):
        """ Parse text into Akoma Ntoso.
        """
        context = ParseContext(pipeline=self.parse_pipeline)
        context.frbr_uri = frbr_uri
        context.fragment_id_prefix = self.fragment_id_prefix
        context.fragment = self.fragment
        context.text = text

        self.parse_pipeline(context)

        return context.xml_text

    def stash_upload(self, upload, f, doc):
        f.seek(0, 2)
        fsize = f.tell()
        f.seek(0)
        attachment = UploadedFile(file=f, name=upload.name, size=fsize, content_type=upload.content_type)
        self.stash_attachment(attachment, doc)

    def stash_imported_attachments(self, context, doc):
        """ Save attachments on the context as real document attachments.
        """
        for att in context.attachments:
            att.file.seek(0, 2)
            fsize = att.file.tell()
            att.file.seek(0)
            upload = UploadedFile(file=att.file, name=att.filename, size=fsize, content_type=att.content_type)
            self.stash_attachment(upload, doc)
            # this ensures that temporary files are deleted
            att.file.close()

    def stash_attachment(self, upload, doc):
        """ Add an UploadedFile instance as an attachment.
        """
        AttachmentSerializer(context={'document': doc}).create({'file': upload})

    def tempfile_for_upload(self, upload):
        """ Uploaded files might not be on disk, ensure it is by creating a temporary file.
        """
        f = tempfile.NamedTemporaryFile()

        self.log.info("Copying uploaded file %s to temp file %s" % (upload, f.name))
        shutil.copyfileobj(upload, f)
        f.flush()
        f.seek(0)

        return f
