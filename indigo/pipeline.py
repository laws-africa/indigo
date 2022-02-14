from whitenoise.storage import CompressedManifestStaticFilesStorage
from pipeline.storage import PipelineMixin


class GzipManifestPipelineStorage(PipelineMixin, CompressedManifestStaticFilesStorage):
    pass
