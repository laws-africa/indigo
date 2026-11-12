import logging

from background_task.management.commands.process_tasks import Command as ProcessTasksCommand


logger = logging.getLogger(__name__)


class Command(ProcessTasksCommand):
    def run(self, *args, **options):
        super().run(*args, **options)
        if options.get('duration', 0) > 0 and not self.sig_manager.kill_now:
            # Failure-based restart policies need a nonzero exit to recycle RAM.
            logger.info('Recycling background worker after its configured duration')
            raise SystemExit(1)
