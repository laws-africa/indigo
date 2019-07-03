import os.path
from shutil import copyfile


def setup_publication_documents(dst_path):
    """ Indigo_api stores some files it its fixtures directory, and those
    are referenced by the fixtures themselves, using relative paths.
    This utility copies those files into dst_path such that the relative
    filenames will continue to work.
    """
    from indigo_api.models import PublicationDocument

    for pubdoc in PublicationDocument.objects.all():
        if pubdoc.file:
            # fixtures are in tests/../fixtures/foo.pdf
            src = os.path.join(
                os.path.dirname(__file__),
                '..',
                pubdoc.file.name)

            dst = os.path.join(dst_path, pubdoc.file.name)
            try:
                os.makedirs(os.path.dirname(dst))
            except OSError as e:
                # 17 means the directory already exists
                if e.errno != 17:
                    raise

            copyfile(src, dst)
