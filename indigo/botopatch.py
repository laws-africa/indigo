import os
from storages.backends.s3boto import S3BotoStorage
from django.conf import settings

# Hack to work around https://github.com/jschneier/django-storages/issues/28
os.environ['S3_USE_SIGV4'] = 'True'


class S3Storage(S3BotoStorage):
    @property
    def connection(self):
        if self._connection is None:
            self._connection = self.connection_class(
                self.access_key, self.secret_key,
                calling_format=self.calling_format, host=settings.AWS_S3_HOST)
        return self._connection
