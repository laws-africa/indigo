from docpipe.pipeline import Stage

from .debate import hierarchicalizeDebate
from .hier import hierarchicalize


class DoctypePipeline(Stage):
    """ Choose a pipeline based on the FRBR URI doctype and subtype.
    """
    pipelines = {
        # default
        '': hierarchicalize,
        'act': hierarchicalize,
        'debate': hierarchicalizeDebate,
    }

    def __call__(self, context):
        pipeline = self.get_pipeline(context.frbr_uri)
        pipeline(context)

    def get_pipeline(self, frbr_uri):
        # act, doc, debate, statement
        doctype = frbr_uri.doctype
        subtype = frbr_uri.subtype

        options = [doctype]
        if subtype:
            options.append(f'{doctype}/{subtype}')

        for option in reversed(options):
            pipeline = self.pipelines.get(option)
            if pipeline:
                return pipeline

        # default
        return self.pipelines['']
