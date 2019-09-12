import datetime

from django.core.management.base import BaseCommand

from indigo_metrics.models import WorkMetrics, DailyWorkMetrics


class Command(BaseCommand):
    help = 'Updates daily metrics for today (or yesterday)'

    def add_arguments(self, parser):
        parser.add_argument('--yesterday', action='store_true')

    def handle(self, *args, **options):
        date = datetime.date.today()
        if options['yesterday']:
            date = date - datetime.timedelta(days=1)

        WorkMetrics.update_all_work_metrics()
        DailyWorkMetrics.update_daily_work_metrics(date)
