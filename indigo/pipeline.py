from __future__ import absolute_import

from whitenoise.django import GzipManifestStaticFilesStorage
from pipeline.storage import PipelineMixin


class GzipManifestPipelineStorage(PipelineMixin, GzipManifestStaticFilesStorage):
    pass
