from __future__ import absolute_import

import subprocess
import tempfile
import shutil
import logging

from django.conf import settings
import mammoth
from cobalt.act import Fragment

from indigo_api.models import Document
from indigo.plugins import plugins, LocaleBasedMatcher


# TODO: move LocaleBasedAnalyzer into a better place
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

    def shell(self, cmd):
        self.log.info("Running %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.log.info("Subprocess exit code: %s, stdout=%d bytes, stderr=%d bytes" % (p.returncode, len(stdout), len(stderr)))

        if stderr:
            self.log.info("Stderr: %s" % stderr.decode('utf-8'))

        return p.returncode, stdout, stderr

    def import_from_upload(self, upload, frbr_uri, request):
        """ Create a new Document by importing it from a
        :class:`django.core.files.uploadedfile.UploadedFile` instance.
        """
        self.reformat = True

        if upload.content_type in ['text/xml', 'application/xml']:
            # just assume it's valid AKN xml
            doc = Document.randomized(frbr_uri)
            doc.content = upload.read().decode('utf-8')
            return doc

        if upload.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            # pre-process docx to HTML and then import html
            html = self.docx_to_html(upload)
            doc = self.import_from_text(html, frbr_uri, '.html')
        elif upload.content_type == 'application/pdf':
            doc = self.import_from_pdf(upload, frbr_uri)
        else:
            # slaw will do its best
            with self.tempfile_for_upload(upload) as f:
                doc = self.import_from_file(f.name, frbr_uri)

        self.analyse_after_import(doc)

        return doc

    def import_from_text(self, input, frbr_uri, suffix=''):
        """ Create a new Document by importing it from plain text.
        """
        with tempfile.NamedTemporaryFile(suffix=suffix) as f:
            self.log.info("INPUT TO SLAW")
            self.log.info(input.encode('utf-8'))
            self.log.info("END INPUT")
            f.write(input.encode('utf-8'))
            f.flush()
            f.seek(0)
            return self.import_from_file(f.name, frbr_uri)

    def import_from_pdf(self, upload, frbr_uri):
        """ Import from a PDF upload.
        """
        with self.tempfile_for_upload(upload) as f:
            # pdf to text
            text = self.pdf_to_text(f)
            if self.reformat:
                text = self.reformat_text(text)

        return self.import_from_text(text, frbr_uri, '.txt')

    def pdf_to_text(self, f):
        cmd = [settings.INDIGO_PDFTOTEXT, "-enc", "UTF-8", "-nopgbrk", "-raw"]

        if self.cropbox:
            # left, top, width, height
            cropbox = (str(int(float(i))) for i in self.cropbox)
            cropbox = zip("-x -y -W -H".split(), cropbox)
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
        return text

    def import_from_file(self, fname, frbr_uri):
        cmd = ['bundle', 'exec', 'slaw', 'parse']

        if self.fragment:
            cmd.extend(['--fragment', self.fragment])
            if self.fragment_id_prefix:
                cmd.extend(['--id-prefix', self.fragment_id_prefix])

        if self.section_number_position:
            cmd.extend(['--section-number-position', self.section_number_position])

        cmd.extend(['--grammar', self.slaw_grammar])
        cmd.append(fname)

        code, stdout, stderr = self.shell(cmd)

        if code > 0:
            raise ValueError(stderr)

        if not stdout:
            raise ValueError("We couldn't get any useful text out of the file")

        self.log.info("OUTPUT FROM SLAW")
        self.log.info(stdout.decode('utf-8'))
        self.log.info("END STDOUT")

        if self.fragment:
            doc = Fragment(stdout.decode('utf-8'))
        else:
            doc = Document.randomized(frbr_uri)
            doc.content = stdout.decode('utf-8')
            doc.frbr_uri = frbr_uri  # reset it
            doc.title = None
            doc.copy_attributes()

        self.log.info("Successfully imported from %s" % fname)
        return doc

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

    def docx_to_html(self, docx_file):
        result = mammoth.convert_to_html(docx_file)
        return result.value
