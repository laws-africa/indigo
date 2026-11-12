from unittest.mock import Mock, patch

from background_task.management.commands import process_tasks as upstream
from background_task.utils import SignalManager
from django.core.management import get_commands, load_command_class
from django.test import SimpleTestCase

from indigo_app.management.commands.process_tasks import Command


class ProcessTasksTestCase(SimpleTestCase):
    def setUp(self):
        self.command = Command()
        # Avoid installing process-wide signal handlers in tests.
        self.command.sig_manager = SignalManager.__new__(SignalManager)
        self.command._tasks = Mock()
        self.command._tasks.run_next_task.return_value = True
        self.autodiscover = patch.object(upstream, 'autodiscover').start()
        self.sleep = patch.object(upstream.time, 'sleep').start()
        self.addCleanup(patch.stopall)

    def test_command_discovery(self):
        self.assertEqual(get_commands()['process_tasks'], 'indigo_app')
        command = load_command_class(get_commands()['process_tasks'], 'process_tasks')
        self.assertIsInstance(command, Command)

    def test_duration_expiry_finishes_task_then_exits_nonzero(self):
        # The first task runs past the deadline; only then does the loop stop.
        with patch.object(upstream, 'time', Mock(time=Mock(side_effect=[0, 0, 43201]))), self.assertLogs(
            'indigo_app.management.commands.process_tasks', level='INFO'
        ) as logs:
            with self.assertRaises(SystemExit) as exit_context:
                self.command.run(duration=43200, queue='indigo')
        self.assertEqual(exit_context.exception.code, 1)
        self.command._tasks.run_next_task.assert_called_once_with('indigo')
        self.assertIn('Recycling background worker', logs.output[0])

    def test_signal_shutdown_returns_normally(self):
        self.command._tasks.run_next_task.side_effect = lambda queue: (
            self.command.sig_manager.exit_gracefully(None, None) or True
        )
        # Check both an active duration and a signal coinciding with expiry.
        for final_time in (1, 43201):
            with self.subTest(final_time=final_time):
                self.command.sig_manager.kill_now = False
                with patch.object(upstream.time, 'time', side_effect=[0, 0, final_time]):
                    self.assertIsNone(self.command.run(duration=43200))
                self.assertTrue(self.command.sig_manager.kill_now)

    def test_unlimited_duration(self):
        for duration in (0, -1):
            with self.subTest(duration=duration):
                self.command.sig_manager.kill_now = False
                self.command._tasks.reset_mock()

                def finish_task(queue):
                    if self.command._tasks.run_next_task.call_count == 2:
                        self.command.sig_manager.exit_gracefully(None, None)
                    return True

                self.command._tasks.run_next_task.side_effect = finish_task
                with patch.object(upstream.time, 'time', return_value=0):
                    self.assertIsNone(self.command.run(duration=duration))
                self.assertEqual(self.command._tasks.run_next_task.call_count, 2)
