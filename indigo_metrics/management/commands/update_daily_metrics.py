import datetime

from django.core.management.base import BaseCommand

from indigo_metrics.models import WorkMetrics, DailyWorkMetrics
from indigo_api.models import Work


class Command(BaseCommand):
    help = 'Updates daily metrics for today (or yesterday)'

    def add_arguments(self, parser):
        parser.add_argument('--yesterday', action='store_true')

    def handle(self, *args, **options):
        date = datetime.date.today()
        if options['yesterday']:
            date = date - datetime.timedelta(days=1)

        self.update_work_metrics()
        self.update_daily_work_metrics(date)

    def update_work_metrics(self):
        self.stdout.write(self.style.SUCCESS('Updating individual work metrics.'))
        for work in Work.objects.all():
            WorkMetrics.create_or_update(work)
        self.stdout.write(self.style.SUCCESS('Done'))

    def update_daily_work_metrics(self, date):
        self.stdout.write(self.style.SUCCESS('Updating aggregate daily work metrics for %s.' % date))
        DailyWorkMetrics.create_or_update(date)
        self.stdout.write(self.style.SUCCESS('Done'))
