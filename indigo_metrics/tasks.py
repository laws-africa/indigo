from datetime import timedelta, date
import logging

from background_task import background
from background_task.models import Task
from django.utils import timezone

from indigo_metrics.models import DailyWorkMetrics, WorkMetrics, DocumentMetrics


# get specific task logger
log = logging.getLogger('indigo.tasks')


@background(queue="indigo", remove_existing_tasks=True)
def update_document_metrics(doc_id):
    DocumentMetrics.create_or_update(doc_id)


@background(queue="indigo", remove_existing_tasks=True)
def update_yesterdays_metrics():
    """ Task to update daily metrics for yesterday. This will replace any existing task.
    """
    try:
        WorkMetrics.update_all_work_metrics()

        yesterday = date.today() - timedelta(days=1)
        DailyWorkMetrics.update_daily_work_metrics(yesterday)
    except Exception as e:
        log.error(f"Error updating work metrics: {e}", exc_info=e)
        raise e


def setup_update_metrics_task(hour=1):
    now = timezone.now()
    at = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if now >= at:
        at = at + timedelta(days=1)
    update_yesterdays_metrics(schedule=at, repeat=Task.DAILY)
