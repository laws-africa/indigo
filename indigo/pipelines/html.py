import logging
import shutil
import tempfile
from zipfile import BadZipFile

import mammoth
from docpipe.pipeline import Stage

from .pipeline import ImportAttachment

log = logging.getLogger(__name__)

WHITELIST = [f'image/{t}' for t in [
    'bmp',
    'gif',
    'jpeg',
    'png',
    'svg+xml',
    'tiff',
    'x-icon',
]]


class DocxToHtml(Stage):
    """ Converts a DOCX file into HTML.

    Reads: context.source_file
    Writes: context.html_text, context.attachments
    """
    def __call__(self, context):
        helper = {'counter': 0}

        def stash_image(image):
            """ Helper that handles an image found in the DOCX file. It stores a corresponding
            attachment on the import context, and gives the file a unique name that is used to
            refer to the image in the HTML.
            """
            helper['counter'] += 1
            try:
                with image.open() as img:
                    # check mimetype first; only process those on our whitelist
                    if image.content_type not in WHITELIST:
                        log.info(f"Image type {image.content_type} not supported; ignoring")
                        return {}

                    # copy the file to somewhere temporary
                    f = tempfile.NamedTemporaryFile()
                    shutil.copyfileobj(img, f)
                    f.seek(0)

                    file_ext = image.content_type.split('/')[1]
                    filename = f'img{helper["counter"]}.{file_ext}'
                    context.attachments.append(ImportAttachment(
                        filename=filename,
                        content_type=image.content_type,
                        file=f,
                    ))
                return {'src': 'media/' + filename}
            except KeyError as e:
                # raised when the image can't be found in the zip file
                log.info(f"Image cannot be found in docx file; ignoring", exc_info=e)
                return {}

        try:
            result = mammoth.convert_to_html(context.source_file, convert_image=mammoth.images.img_element(stash_image))
            html = result.value
        except BadZipFile:
            raise ValueError("This doesn't seem to be a valid DOCX file.")

        context.html_text = html
