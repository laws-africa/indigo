import datetime

from django.test import TestCase

from indigo_api.models import Work
from indigo_metrics.models import WorkMetrics, DailyWorkMetrics


class DailyWorkMetricsTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work', 'drafts', 'published']

    def test_metrics(self):
        for work in Work.objects.all():
            WorkMetrics.create_or_update(work)

        date = datetime.date(2019, 2, 1)

        DailyWorkMetrics.create_or_update(date)

        dailies = DailyWorkMetrics.objects.filter(date=date).all()
        self.assertEqual(len(dailies), 2)
