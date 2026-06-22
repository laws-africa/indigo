import logging

from django.test import SimpleTestCase

from indigo_app.logging import (
    LoggingContextFilter,
    clear_log_context,
    log_context,
    set_log_context,
)
from indigo_app.middleware import LogContextMiddleware


class LoggingContextFilterTest(SimpleTestCase):
    def setUp(self):
        self.filter = LoggingContextFilter()
        clear_log_context()

    def tearDown(self):
        clear_log_context()

    def make_record(self, **kwargs):
        record = logging.makeLogRecord(kwargs)
        self.filter.filter(record)
        return record

    def test_uses_request_id_without_task_context(self):
        record = self.make_record(request_id="request-1")

        self.assertEqual(LoggingContextFilter.empty, record.task_run_id)
        self.assertEqual(LoggingContextFilter.empty, record.task_name)
        self.assertEqual("request-1", record.correlation_id)
        self.assertEqual(LoggingContextFilter.empty, record.frbr_uri)

    def test_empty_value_can_be_configured(self):
        self.filter = LoggingContextFilter(empty="-")
        record = self.make_record()

        self.assertEqual(LoggingContextFilter.empty, record.task_run_id)
        self.assertEqual(LoggingContextFilter.empty, record.task_name)
        self.assertEqual(LoggingContextFilter.empty, record.correlation_id)
        self.assertEqual(LoggingContextFilter.empty, record.frbr_uri)

    def test_empty_value_can_be_configured_on_the_class(self):
        old_empty = LoggingContextFilter.empty
        try:
            LoggingContextFilter.empty = "x"
            self.filter = LoggingContextFilter()
            record = self.make_record()
        finally:
            LoggingContextFilter.empty = old_empty

        self.assertEqual("x", record.task_run_id)
        self.assertEqual("x", record.task_name)
        self.assertEqual("x", record.correlation_id)
        self.assertEqual("x", record.frbr_uri)

    def test_uses_task_run_id_as_correlation_id(self):
        with log_context(task_run_id="task-1", task_name="indigo_app.tasks.example"):
            record = self.make_record(request_id="request-1")

        self.assertEqual("task-1", record.task_run_id)
        self.assertEqual("indigo_app.tasks.example", record.task_name)
        self.assertEqual("task-1", record.correlation_id)

    def test_restores_nested_contexts(self):
        with log_context(task_run_id="outer"):
            with log_context(task_run_id="inner"):
                self.assertEqual("inner", self.make_record().task_run_id)

            self.assertEqual("outer", self.make_record().task_run_id)

        self.assertEqual(LoggingContextFilter.empty, self.make_record().task_run_id)

    def test_set_log_context_sets_context_until_cleared(self):
        set_log_context(frbr_uri="/akn/za/judgment/1")

        self.assertEqual("/akn/za/judgment/1", self.make_record().frbr_uri)

        clear_log_context()
        self.assertEqual(LoggingContextFilter.empty, self.make_record().frbr_uri)

    def test_none_values_do_not_replace_existing_context(self):
        with log_context(
            task_run_id="task-1",
            task_name="indigo_app.tasks.example",
            frbr_uri="/akn/za/judgment/1",
        ):
            with log_context(task_name=None, frbr_uri=None):
                record = self.make_record()

        self.assertEqual("task-1", record.task_run_id)
        self.assertEqual("indigo_app.tasks.example", record.task_name)
        self.assertEqual("/akn/za/judgment/1", record.frbr_uri)

    def test_context_is_additive(self):
        with log_context(task_run_id="task-1", task_name="indigo_app.tasks.example"):
            with log_context(frbr_uri="/akn/za/judgment/1"):
                record = self.make_record()

        self.assertEqual("task-1", record.task_run_id)
        self.assertEqual("indigo_app.tasks.example", record.task_name)
        self.assertEqual("/akn/za/judgment/1", record.frbr_uri)

    def test_log_context_can_be_used_as_a_decorator(self):
        @log_context(task_run_id="decorated")
        def get_task_run_id():
            return self.make_record().task_run_id

        self.assertEqual("decorated", get_task_run_id())
        self.assertEqual(LoggingContextFilter.empty, self.make_record().task_run_id)

    def test_log_context_rejects_unknown_context_keys(self):
        with self.assertRaises(TypeError):
            log_context(task_id="task-1")

    def test_middleware_clears_context_before_and_after_request(self):
        def get_response(request):
            self.assertEqual(LoggingContextFilter.empty, self.make_record().frbr_uri)
            set_log_context(frbr_uri="/akn/za/judgment/1")
            return object()

        set_log_context(frbr_uri="/akn/za/judgment/stale")

        response = LogContextMiddleware(get_response)(object())

        self.assertIsNotNone(response)
        self.assertEqual(LoggingContextFilter.empty, self.make_record().frbr_uri)
