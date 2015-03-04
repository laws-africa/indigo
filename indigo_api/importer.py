import subprocess
import tempfile
import shutil
import logging

from .models import Document

class Importer(object):
    log = logging.getLogger(__name__)

    def import_from_upload(self, upload):
        """ Create a new Document by importing it from a
        :class:`django.core.files.uploadedfile.UploadedFile` instance.
        """
        # we got a file
        if upload.content_type == 'application/pdf':
            with self.tempfile_for_upload(upload) as f:
                doc = self.import_from_pdf(f.name)

            if not doc.title:
                doc.title = "Imported from %s" % upload.name

        elif upload.content_type in ['text/xml', 'application/xml']:
            doc = Document()
            doc.content = upload.read().decode('utf-8')

        else:
            # bad type of file
            raise ValueError('Only PDF and XML files are supported.')

        # TODO: handle doc input
        # TODO: handle plain text input

        return doc

    def import_from_pdf(self, pdf):
        # TODO:
        # TODO: handle errors
        cmd = 'slaw convert --output xml --input pdf'.split(' ') + [pdf]
        self.log.info("Running %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        self.log.info("Subprocess exit code: %s" % p.returncode)
        if p.returncode > 0:
            raise ValueError("Error converting file: %s" % stderr)

        doc = Document()
        doc.content = stdout

        self.log.info("Successfully imported")
        return doc

    def tempfile_for_upload(self, upload):
        """ Uploaded files might not be on disk. If not, create temporary file. """
        if hasattr(upload, 'temporary_file_path'):
            return upload

        f = tempfile.NamedTemporaryFile()

        self.log.info("Copying uploaded file %s to temp file %s" % (upload, f.name))
        shutil.copyfileobj(upload, f)
        f.flush()
        f.seek(0)

        return f
