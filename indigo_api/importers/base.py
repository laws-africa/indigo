# -*- coding: utf-8 -*-
import subprocess
import tempfile
import shutil
import logging
import re
from zipfile import BadZipFile

from django.conf import settings
from django.core.files.base import ContentFile
import mammoth
import lxml.etree as ET
from django.core.files.uploadedfile import UploadedFile

from cobalt import AkomaNtosoDocument
from indigo_api.models import Attachment
from indigo.plugins import plugins, LocaleBasedMatcher
from indigo_api.serializers import AttachmentSerializer
from indigo_api.utils import filename_candidates, find_best_static
from indigo_api.importers.pdfs import pdf_extract_pages


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
    """
    Import from PDF and other document types using Slaw.

    Slaw is a commandline tool from the slaw Ruby Gem which generates Akoma Ntoso
    from PDF and other documents. See https://rubygems.org/gems/slaw
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

    reformat = False
    """ Should we tell Slaw to reformat before parsing? Only do this with initial imports. """

    cropbox = None
    """ Crop box to import within, as [left, top, width, height]
    """

    slaw_grammar = 'za'
    """ Slaw grammar to use
    """

    use_ascii = True
    """ Should we pass --ascii to slaw? This can have significant performance benefits
    for large files. See https://github.com/cjheath/treetop/issues/31
    """

    page_nums = None
    """ Pages to import for document types that support it, or None to import them all.
    
    This can either be a string, such as "1,5,7-11" or it can be a list of integers and (first, last) tuples.
    """

    def shell(self, cmd):
        self.log.info("Running %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.log.info("Subprocess exit code: %s, stdout=%d bytes, stderr=%d bytes" % (p.returncode, len(stdout), len(stderr)))

        if stderr:
            self.log.info("Stderr: %s" % stderr.decode('utf-8'))

        return p.returncode, stdout, stderr

    def create_from_upload(self, upload, doc, request):
        """ Create a new Document by importing it from a
        :class:`django.core.files.uploadedfile.UploadedFile` instance.
        """
        self.reformat = True
        self.log.info("Processing upload: filename='%s', content type=%s" % (upload.name, upload.content_type))

        if upload.content_type in ['text/xml', 'application/xml']:
            self.log.info("Processing upload as an AKN XML file")
            self.create_from_akn(upload, doc)

        elif (upload.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                or upload.name.endswith('.docx')):
            # pre-process docx to HTML and then import html
            self.log.info("Processing upload as a docx file")
            self.create_from_docx(upload, doc)

        elif upload.content_type == 'application/pdf':
            self.log.info("Processing upload as a PDF file")
            self.create_from_pdf(upload, doc)

        elif upload.content_type == 'text/html':
            self.log.info("Processing upload as an HTML file")
            self.create_from_html(upload, doc)

        else:
            # slaw will do its best
            self.log.info("Processing upload as an unknown file")
            self.create_from_file(upload, doc, 'text')

        self.analyse_after_import(doc)

    def create_from_akn(self, upload, doc):
        # just assume it's valid AKN xml
        doc.content = upload.read().decode('utf-8')
        self.stash_attachment(upload, doc)

    def create_from_file(self, upload, doc, inputtype):
        with self.tempfile_for_upload(upload) as f:
            xml = self.import_from_file(f.name, doc.frbr_uri, inputtype)
            doc.reset_xml(xml, from_model=True)
            self.stash_attachment(upload, doc)

    def create_from_html(self, upload, doc):
        """ Apply an XSLT to map the HTML to text, then process the text with Slaw.
        """
        text = self.html_to_text(upload.read().decode('utf-8'), doc)
        if self.reformat:
            text = self.reformat_text_from_html(text)
        xml = self.import_from_text(text, doc.frbr_uri, 'text')
        doc.reset_xml(xml, from_model=True)
        self.stash_attachment(upload, doc)

    def html_to_text(self, html, doc):
        """ Transform HTML (a str) into Akoma-Ntoso friendly text (str).
        """
        candidates = filename_candidates(doc, prefix='xsl/html_to_akn_text_', suffix='.xsl')
        xslt_filename = find_best_static(candidates)
        if not xslt_filename:
            raise ValueError("Couldn't find XSLT file to use for %s, tried: %s" % (doc, candidates))

        html = ET.HTML(html)
        xslt = ET.XSLT(ET.parse(xslt_filename))
        result = xslt(html)
        return str(result)

    def import_from_text(self, input, frbr_uri, suffix=''):
        """ Create a new Document by importing it from plain text.
        """
        with tempfile.NamedTemporaryFile(suffix=suffix) as f:
            f.write(input.encode('utf-8'))
            f.flush()
            f.seek(0)
            inputtype = 'html' if suffix == '.html' else 'text'
            return self.import_from_file(f.name, frbr_uri, inputtype)

    def create_from_pdf(self, upload, doc):
        """ Import from a PDF upload.
        """
        with self.tempfile_for_upload(upload) as f:
            # extract pages
            if self.page_nums:
                if isinstance(self.page_nums, str):
                    self.page_nums = parse_page_nums(self.page_nums)
                if self.page_nums:
                    pdf_extract_pages(f.name, self.page_nums, f.name)

            # pdf to text
            text = self.pdf_to_text(f)
            if self.reformat:
                text = self.reformat_text_from_pdf(text)
            if len(text) < 512:
                raise ValueError("There is not enough text in the PDF to import. You may need to OCR the file first.")

            xml = self.import_from_text(text, doc.frbr_uri, '.txt')
            doc.reset_xml(xml, from_model=True)

            # stash the (potentially) modified pdf file
            f.seek(0, 2)
            fsize = f.tell()
            f.seek(0)
            pdf = UploadedFile(file=f, name=upload.name, size=fsize, content_type=upload.content_type)
            self.stash_attachment(pdf, doc)

    def pdf_to_text(self, f):
        cmd = [settings.INDIGO_PDFTOTEXT, "-enc", "UTF-8", "-nopgbrk", "-raw"]

        if self.cropbox:
            # left, top, width, height
            cropbox = (str(int(float(i))) for i in self.cropbox)
            cropbox = list(zip("-x -y -W -H".split(), cropbox))
            # flatten
            cmd += [x for pair in cropbox for x in pair]

        cmd += [f.name, '-']
        code, stdout, stderr = self.shell(cmd)

        if code > 0:
            raise ValueError(stderr)

        return stdout.decode('utf-8')

    def reformat_text(self, text):
        """ Clean up extracted text before giving it to Slaw.
        """
        text = self.expand_ligatures(text)
        return text

    def reformat_text_from_html(self, text):
        return self.reformat_text(text)

    def reformat_text_from_pdf(self, text):
        return self.reformat_text(text)

    def import_from_file(self, fname, frbr_uri, inputtype):
        cmd = ['bundle', 'exec', 'slaw', 'parse']

        if self.fragment:
            cmd.extend(['--fragment', self.fragment])
            if self.fragment_id_prefix:
                cmd.extend(['--id-prefix', self.fragment_id_prefix])

        if self.section_number_position:
            cmd.extend(['--section-number-position', self.section_number_position])

        cmd.extend(['--grammar', self.slaw_grammar])
        cmd.extend(['--input', inputtype])
        if self.use_ascii:
            cmd.extend(['--ascii'])
        cmd.append(fname)

        code, stdout, stderr = self.shell(cmd)

        if code > 0:
            raise ValueError(stderr.decode('utf-8'))

        if not stdout:
            raise ValueError("We couldn't get any useful text out of the file")

        xml = stdout.decode('utf-8')
        self.log.info("Successfully imported from %s" % fname)

        return self.postprocess(xml, frbr_uri)

    def tempfile_for_upload(self, upload):
        """ Uploaded files might not be on disk, ensure it is by creating a
        temporary file.
        """
        f = tempfile.NamedTemporaryFile()

        self.log.info("Copying uploaded file %s to temp file %s" % (upload, f.name))
        shutil.copyfileobj(upload, f)
        f.flush()
        f.seek(0)

        return f

    def analyse_after_import(self, doc):
        """ Run analysis after import.
        Usually only used on PDF documents.
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

    def create_from_docx(self, docx_file, doc):
        """ We can create a mammoth image handler that stashes the binary data of the image
        and returns an appropriate img attribute to be put into the HTML (and eventually xml).
        Once the document is created, we can then create attachments with the stashed image data,
        and set appropriate filenames.
        """
        # we need an id to associate attachments
        if doc.id is None:
            doc.save()

        self.counter = 0

        def stash_image(image):
            self.counter += 1
            try:
                with image.open() as img:
                    content = img.read()
                    image_type = image.content_type
                    file_ext = image_type.split('/')[1]
                    cf = ContentFile(content)

                    att = Attachment()
                    att.filename = 'img{num}.{extension}'.format(num=self.counter, extension=file_ext)
                    att.mime_type = image_type
                    att.document = doc
                    att.size = cf.size
                    att.content = cf
                    att.file.save(att.filename, cf)
            except KeyError:
                # raised when the image can't be found in the zip file
                return {}

            return {
                'src': 'media/' + att.filename
            }

        try:
            result = mammoth.convert_to_html(docx_file, convert_image=mammoth.images.img_element(stash_image))
            html = result.value
        except BadZipFile:
            raise ValueError("This doesn't seem to be a valid DOCX file.")

        xml = self.import_from_html(html, doc.frbr_uri)
        doc.reset_xml(xml, from_model=True)
        self.stash_attachment(docx_file, doc)

    def import_from_html(self, html, frbr_uri):
        return self.import_from_text(html, frbr_uri, '.html')

    def expand_ligatures(self, text):
        """ Replace ligatures with separate characters, eg. ﬁ -> fi.
        """
        return text\
            .replace('ﬁ', 'fi')\
            .replace('ﬀ', 'ff')\
            .replace('ﬃ', 'ffi')\
            .replace('ﬄ', 'ffl')\
            .replace('ﬆ', 'st')\
            .replace('ı', 'i')

    def stash_attachment(self, upload, doc):
        # add source file as an attachment
        AttachmentSerializer(context={'document': doc}).create({'file': upload})

    def postprocess(self, xml, frbr_uri):
        """ Post-process raw XML generated by the importer.
        """
        # clean up encoding string in XML produced by slaw
        doc = AkomaNtosoDocument(xml)
        return doc.to_xml(encoding='unicode')
