import subprocess
import tempfile
import shutil
import logging

from django.conf import settings

from .models import Document
from cobalt.act import Fragment


class Slaw(object):
    log = logging.getLogger(__name__)

    def link_terms(self, document):
        """
        Find and link defined terms in a document.
        """
        with tempfile.NamedTemporaryFile() as f:
            f.write(document.content)
            f.flush()
            cmd = ['link-definitions', f.name]
            code, stdout, stderr = self.slaw(cmd)
            if code > 0:
                raise ValueError(stderr)
            document.content = stdout

        return stdout

    def slaw(self, args):
        """ Call slaw with ``args`` """
        cmd = ['bundle', 'exec', 'slaw'] + args
        self.log.info("Running %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.log.info("Subprocess exit code: %s, stdout=%d bytes, stderr=%d bytes" % (p.returncode, len(stdout), len(stderr)))

        if stderr:
            self.log.info("Stderr: %s" % stderr.decode('utf-8'))

        return p.returncode, stdout, stderr


class Importer(Slaw):
    """
    Import from PDF and other document types using Slaw.

    Slaw is a commandline tool from the slaw Ruby Gem which generates Akoma Ntoso
    from PDF and other documents. See https://rubygems.org/gems/slaw
    """

    """ The name of the AKN element that we're importing, or None for a full act. """
    fragment = None

    """ The prefix for all ids generated for this fragment """
    fragment_id_prefix = None

    """ By default, where do section numbers usually lie in relation to their
    title? One of: ``before-title``, ``after-title`` or ``guess``.
    """
    section_number_position = 'before-title'

    """ Should we tell Slaw to reformat before parsing? Only do this with initial imports. """
    reformat = False

    def import_from_upload(self, upload, request):
        """ Create a new Document by importing it from a
        :class:`django.core.files.uploadedfile.UploadedFile` instance.
        """
        if upload.content_type in ['text/xml', 'application/xml']:
            doc = Document.randomized(request.user)
            doc.content = upload.read().decode('utf-8')
        else:
            with self.tempfile_for_upload(upload) as f:
                self.reformat = True
                doc = self.import_from_file(f.name, request)

            if not self.fragment:
                doc.title = "Imported from %s" % upload.name
                doc.copy_attributes()

        return doc

    def import_from_text(self, input, request):
        """ Create a new Document by importing it from plain text.
        """
        with tempfile.NamedTemporaryFile() as f:
            f.write(input.encode('utf-8'))
            f.flush()
            f.seek(0)
            doc = self.import_from_file(f.name, request)

        return doc

    def import_from_file(self, fname, request):
        cmd = ['parse', '--no-definitions']

        if self.fragment:
            cmd.extend(['--fragment', self.fragment])
            if self.fragment_id_prefix:
                cmd.extend(['--id-prefix', self.fragment_id_prefix])

        if self.reformat:
            cmd.extend(['--reformat'])

        if self.section_number_position:
            cmd.extend(['--section-number-position', self.section_number_position])

        cmd.extend(['--pdftotext', settings.INDIGO_PDFTOTEXT])
        cmd.append(fname)

        code, stdout, stderr = self.slaw(cmd)

        if code > 0:
            raise ValueError(stderr)

        if not stdout:
            raise ValueError("We couldn't get any useful text out of the file")

        if self.fragment:
            doc = Fragment(stdout.decode('utf-8'))
        else:
            doc = Document.randomized(request.user)
            frbr_uri = doc.frbr_uri
            doc.content = stdout.decode('utf-8')
            doc.frbr_uri = frbr_uri  # reset it
            doc.copy_attributes()

        self.log.info("Successfully imported from %s" % fname)
        return doc

    def tempfile_for_upload(self, upload):
        """ Uploaded files might not be on disk. If not, create temporary file. """
        if hasattr(upload, 'temporary_file_path'):
            return upload.file

        f = tempfile.NamedTemporaryFile()

        self.log.info("Copying uploaded file %s to temp file %s" % (upload, f.name))
        shutil.copyfileobj(upload, f)
        f.flush()
        f.seek(0)

        return f
