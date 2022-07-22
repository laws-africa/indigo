import logging
import subprocess

log = logging.getLogger(__name__)


class ImportAttachment:
    def __init__(self, filename, content_type, file):
        self.filename = filename
        self.content_type = content_type
        self.file = file


# TODO: I think python3 has a better way of doing this
def shell(cmd):
    log.info("Running %s" % cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    log.info("Subprocess exit code: %s, stdout=%d bytes, stderr=%d bytes" % (p.returncode, len(stdout), len(stderr)))

    if stderr:
        log.info("Stderr: %s" % stderr.decode('utf-8'))

    return p.returncode, stdout, stderr
