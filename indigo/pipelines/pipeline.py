import logging
import subprocess

log = logging.getLogger(__name__)


class PipelineContext:
    def __init__(self, pipeline):
        self.pipeline = pipeline


class Stage:
    def get_name(self):
        return getattr(self, 'name', self.__class__.__name__)

    def get_description(self):
        return getattr(self, 'description', self.__class__.__doc__)

    def __call__(self, context):
        # must be implemented and modify items in the context
        pass


class Pipeline(Stage):
    """ A pipeline is a series of Stage objects that are called in order.

    A pipeline is itself a stage which allows nesting of pipelines.
    """
    def __init__(self, stages=None):
        super().__init__()
        self.stages = stages or []

    def add(self, stage):
        self.stages.append(stage)

    def __call__(self, context):
        self.before(context)

        for stage in self.stages:
            self.before_stage(stage, context)
            stage(context)
            self.after_stage(stage, context)

        self.after(context)

    def before(self, context):
        pass

    def after(self, context):
        pass

    def before_stage(self, stage, context):
        pass

    def after_stage(self, stage, context):
        pass


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
