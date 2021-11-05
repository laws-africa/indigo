from datetime import timedelta
import logging

from background_task import background
from background_task.models import Task

from indigo_api.models import Document

# get specific task logger
log = logging.getLogger('indigo.tasks')


@background(queue="indigo", remove_existing_tasks=True)
def prune_deleted_documents():
    """ Task to prune old deleted documents.
    """
    try:
        Document.prune_deleted_documents()
    except Exception as e:
        log.error(f"Error pruning deleted documents: {e}", exc_info=e)
        raise e


def setup_prune_deleted_documents():
    # schedule task to run in 12 hours time, and repeat daily
    prune_deleted_documents(schedule=timedelta(hours=12), repeat=Task.DAILY)
