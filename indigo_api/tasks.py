import os
import socket
from datetime import timedelta
import logging
from uuid import uuid4

import sentry_sdk
from django.conf import settings
from django.db import transaction
from sentry_sdk.tracing import TRANSACTION_SOURCE_TASK
from background_task import background
from background_task.signals import task_error
from background_task.tasks import DBTaskRunner, logger, tasks
from background_task.models import Task
from django.db.utils import OperationalError
from django.dispatch import receiver

from indigo_api.models import Document, DocumentActivity
from indigo_app.logging import log_context, clear_log_context

# get specific task logger
log = logging.getLogger('indigo.tasks')


class PatchedDBTaskRunner(DBTaskRunner):
    """Patch DBTaskRunner to be more efficient when pulling tasks from the database. This can be dropped once
    https://github.com/arteria/django-background-tasks/pull/244/files is merged into django-background-task.
    """
    def __init__(self):
        super().__init__()
        # ensure hostname is included in worker name because pid is not unique across docker containers
        self.worker_name = f"{socket.gethostname()}-{os.getpid()}"

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
        clear_log_context()
        try:
            # wrap the task in a sentry transaction
            with sentry_sdk.start_transaction(
                    op="queue.task", source=TRANSACTION_SOURCE_TASK, name=task.task_name
            ) as transaction:
                transaction.set_status("ok")
                with log_context(
                        task_run_id=task_run_id(task), task_name=task.task_name
                ):
                    super().run_task(tasks, task)
        finally:
            clear_log_context()


# use the patched runner
tasks._runner = PatchedDBTaskRunner()


def _task_str(self):
    return f"Task<#{self.pk} {self.task_name} params={self.task_params}>"


# override Task.__str__ so it's more description
Task.__str__ = _task_str


# this is a logging fingerprint for a task run
def task_run_id(task):
    nonce = uuid4().hex[:6]
    return f"task:{settings.INDIGO['APP_NAME'].lower()}:{task.pk}:{task.task_name}:{nonce}"


@receiver(task_error)
def on_task_error(*args, **kwargs):
    # report the exception to Sentry
    hub = sentry_sdk.Hub.current
    hub.capture_exception()

    # now mark the current transaction as handled, otherwise it'll be reported twice
    if hub.scope and hub.scope.transaction:
        hub.scope.transaction.timestamp = -1


@background(queue="indigo", remove_existing_tasks=True)
@transaction.atomic
def prune_deleted_documents():
    """ Task to prune old deleted documents.
    """
    try:
        Document.prune_deleted_documents()
    except Exception as e:
        log.error(f"Error pruning deleted documents: {e}", exc_info=e)
        raise e


@background(queue="indigo", remove_existing_tasks=True)
@transaction.atomic
def prune_document_versions():
    """ Prune out old document versions.
    """
    try:
        Document.prune_document_versions()
    except Exception as e:
        log.error(f"Error pruning document versions: {e}", exc_info=e)
        raise e


@background(queue="indigo", remove_existing_tasks=True)
@transaction.atomic
def prune_document_activity():
    """ Prune out old DocumentActivity entries.
    """
    try:
        DocumentActivity.vacuum()
    except Exception as e:
        log.error(f"Error pruning document activity: {e}", exc_info=e)
        raise e


def setup_pruning():
    # schedule task to run in 12 hours time, and repeat daily
    prune_deleted_documents(schedule=timedelta(hours=11), repeat=Task.DAILY)

    # schedule task to run in 12 hours time, and repeat daily
    prune_document_versions(schedule=timedelta(hours=12), repeat=Task.DAILY)

    # schedule task to run in 12 hours time, and repeat daily
    prune_document_activity(schedule=timedelta(hours=13), repeat=Task.DAILY)
