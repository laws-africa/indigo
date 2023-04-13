from django.conf import settings
from django.dispatch import receiver
from background_task.signals import task_started, task_successful, task_error, task_finished
import sentry_sdk


# monitor background tasks
@receiver(task_started)
def bg_task_started(sender, **kwargs):
    if not settings.DEBUG and settings.SENTRY_DSN:
        transaction = sentry_sdk.start_transaction(op="queue.task.bg")
        transaction.set_tag("transaction_type", "task")
        # fake an entry into the context
        transaction.__enter__()


@receiver(task_successful)
def bg_task_success(sender, completed_task, **kwargs):
    if not settings.DEBUG and settings.SENTRY_DSN:
        transaction = sentry_sdk.Hub.current.scope.transaction
        if transaction:
            transaction.name = completed_task.task_name


# capture background tasks errors
@receiver(task_error)
def bg_task_error(sender, task, **kwargs):
    if not settings.DEBUG and settings.SENTRY_DSN:
        transaction = sentry_sdk.Hub.current.scope.transaction
        if transaction:
            transaction.name = task.task_name

        sentry_sdk.capture_exception()


@receiver(task_finished)
def bg_task_finished(sender, **kwargs):
    if not settings.DEBUG and settings.SENTRY_DSN:
        transaction = sentry_sdk.Hub.current.scope.transaction
        if transaction:
            # fake an exit from the transaction context
            transaction.__exit__(None, None, None)
