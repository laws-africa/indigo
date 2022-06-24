import logging

from django.core.management.base import BaseCommand

from indigo_api.models import Document
from indigo_metrics.models import DocumentMetrics


log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update DocumentMetrics for each undeleted document.'

    def handle(self, *args, **options):
        for document in Document.objects.filter(deleted=False).order_by('-pk'):
            DocumentMetrics.create_or_update(document.pk)
            log.info(f"DocumentMetrics updated for document #{document.pk}.")
