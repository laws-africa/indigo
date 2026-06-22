"""Thread-local logging context helpers.

Some useful log metadata is only known deep in a request or task, far away from
where log records are emitted. Store that metadata here and
``LoggingContextFilter`` will copy it onto every log record for the current
thread/async context.

Context is cleared at request and task boundaries. This means unscoped calls to
``set_log_context`` are safe for places such as Django admin hooks, but code
that can naturally scope the value should prefer ``log_context``.
"""

import logging
from contextlib import contextmanager

try:
    from asgiref.local import Local
except ImportError:
    from threading import local as Local


local = Local()
LOG_CONTEXT_KEYS = ("task_run_id", "task_name", "frbr_uri")


def _context_values(task_run_id=None, task_name=None, frbr_uri=None):
    return {
        key: value
        for key, value in {
            "task_run_id": task_run_id,
            "task_name": task_name,
            "frbr_uri": frbr_uri,
        }.items()
        if value is not None
    }


def set_log_context(task_run_id=None, task_name=None, frbr_uri=None):
    """Set log context fields until they are overwritten or explicitly cleared.

    Only explicit, non-None values are applied. Passing ``None`` is a no-op so
    callers can add optional context without accidentally erasing context set by
    an outer request or task.
    """

    for key, value in _context_values(
        task_run_id=task_run_id, task_name=task_name, frbr_uri=frbr_uri
    ).items():
        setattr(local, key, value)


def clear_log_context():
    """Clear all known log context fields.

    This should be called at lifecycle boundaries such as the start and end of a
    request or background task to prevent thread-local context leaking into the
    next unit of work.
    """

    for key in LOG_CONTEXT_KEYS:
        try:
            delattr(local, key)
        except AttributeError:
            pass


@contextmanager
def log_context(task_run_id=None, task_name=None, frbr_uri=None):
    """Temporarily set log context for a block or decorated function.

    The previous values for any supplied fields are restored afterwards, making
    this suitable for nested task/document operations. Use ``set_log_context``
    instead when the code path cannot be wrapped cleanly.
    """

    kwargs = _context_values(
        task_run_id=task_run_id, task_name=task_name, frbr_uri=frbr_uri
    )
    missing = object()
    old_values = {key: getattr(local, key, missing) for key in kwargs}
    try:
        set_log_context(task_run_id=task_run_id, task_name=task_name, frbr_uri=frbr_uri)
        yield
    finally:
        for key, value in old_values.items():
            if value is missing:
                try:
                    delattr(local, key)
                except AttributeError:
                    pass
            else:
                setattr(local, key, value)


class LoggingContextFilter(logging.Filter):
    """Attach request/task/document context fields to log records.

    ``request_id`` comes from django-log-request-id. ``task_run_id``,
    ``task_name`` and ``frbr_uri`` come from this module's local context.
    ``correlation_id`` is the task run id when present, otherwise the request
    id.
    """

    empty = "-"

    def __init__(self, name="", empty=None):
        """Create the filter.

        ``empty`` overrides the class-level fallback for missing fields. It can
        be passed from ``settings.LOGGING`` as a filter constructor kwarg, for
        example ``{"()": "...LoggingContextFilter", "empty": "-"}``.
        """

        super().__init__(name)
        if empty is not None:
            self.empty = empty

    def filter(self, record):
        task_run_id = getattr(local, "task_run_id", None)
        record.task_run_id = task_run_id or self.empty
        record.task_name = getattr(local, "task_name", None) or self.empty
        record.correlation_id = (
            task_run_id or getattr(record, "request_id", None) or self.empty
        )
        record.frbr_uri = getattr(local, "frbr_uri", None) or self.empty
        return True
