class Importer(object):
    def import_from_upload(upload):
        """ Create a new Document by importing it from a
        :class:`django.core.files.uploadedfile.UploadedFile` instance.
        """
        # we got a file
        if upload.content_type == 'application/pdf':
            document = Document()
            # TODO: do import
            document.title = "Imported from %s" % upload.name

        elif upload.content_type in ['text/xml', 'application/xml']:
            document = Document()
            document.content = upload.read().decode('utf-8')

        else:
            # bad type of file
            raise ValueError('Only PDF and XML files are supported.')

        # TODO: handle doc input
        # TODO: handle plain text input

        return document
