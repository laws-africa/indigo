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
        if upload.content_type == 'application/pdf':
            doc = self.import_from_file_upload(upload, 'pdf')

        elif upload.content_type == "text/plain":
            doc = self.import_from_file_upload(upload, 'text')

        elif upload.content_type in ['text/xml', 'application/xml']:
            doc = Document()
            doc.content = upload.read().decode('utf-8')

        else:
            # bad type of file
            raise ValueError('Unsupported file type: %s' % upload.content_type)

        # TODO: handle doc input

        return doc

    def import_from_file_upload(self, upload, ftype):
        with self.tempfile_for_upload(upload) as f:
            doc = self.import_from_file(f.name, ftype)

        if not doc.title:
            doc.title = "Imported from %s" % upload.name

        return doc

    def import_from_file(self, fname, ftype):
        cmd = ('convert --output xml --input %s' % ftype).split(' ')
        code, stdout, stderr = self.slaw(cmd + [fname])
        if code > 0:
            raise ValueError("Error converting file: %s" % stderr)

        doc = Document()
        doc.content = stdout.decode('utf-8')

        self.log.info("Successfully imported from %s" % fname)
        return doc

    def slaw(self, args):
        cmd = ['slaw'] + args
        self.log.info("Running %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.log.info("Subprocess exit code: %s" % p.returncode)

        return p.returncode, stdout, stderr


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
