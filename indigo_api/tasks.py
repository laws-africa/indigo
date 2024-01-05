from datetime import timedelta
import logging

import sentry_sdk
from sentry_sdk.tracing import Transaction, TRANSACTION_SOURCE_TASK
from background_task import background
from background_task.tasks import DBTaskRunner, logger, tasks
from background_task.models import Task
from django.db.utils import OperationalError

from indigo_api.models import Document

# get specific task logger
log = logging.getLogger('indigo.tasks')


class PatchedDBTaskRunner(DBTaskRunner):
    """Patch DBTaskRunner to be more efficient when pulling tasks from the database. This can be dropped once
    https://github.com/arteria/django-background-tasks/pull/244/files is merged into django-background-task.
    """

    def get_task_to_run(self, tasks, queue=None):
        try:
            # This is the changed line
            available_tasks = Task.objects.find_available(queue).filter(
                task_name__in=tasks._tasks
            )[:5]
            for task in available_tasks:
                # try to lock task
                locked_task = task.lock(self.worker_name)
                if locked_task:
                    return locked_task
            return None
        except OperationalError:
            logger.warning("Failed to retrieve tasks. Database unreachable.")

    def run_task(self, tasks, task):
        # wrap the task in a sentry transaction
        transaction = Transaction(op="queue.task", source=TRANSACTION_SOURCE_TASK, name=task.task_name)
        transaction.set_status("ok")
        with sentry_sdk.start_transaction(transaction):
            super().run_task(tasks, task)


# use the patched runner
tasks._runner = PatchedDBTaskRunner()


@background(queue="indigo", remove_existing_tasks=True)
def prune_deleted_documents():
    """ Task to prune old deleted documents.
    """
    try:
        Document.prune_deleted_documents()
    except Exception as e:
        log.error(f"Error pruning deleted documents: {e}", exc_info=e)
        raise e


@background(queue="indigo", remove_existing_tasks=True)
def prune_document_versions():
    """ Prune out old document versions.
    """
    try:
        Document.prune_document_versions()
    except Exception as e:
        log.error(f"Error pruning document versions: {e}", exc_info=e)
        raise e


def setup_pruning():
    # schedule task to run in 12 hours time, and repeat daily
    prune_deleted_documents(schedule=timedelta(hours=12), repeat=Task.DAILY)

    # schedule task to run in 12 hours time, and repeat daily
    prune_document_versions(schedule=timedelta(hours=12), repeat=Task.DAILY)
