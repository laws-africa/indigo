# -*- coding: utf-8 -*-
from django.test import TestCase

from indigo_api.models import Work
from indigo_metrics.models import WorkMetrics


class WorkMetricsTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work', 'drafts', 'published']

    def test_metrics_for_all_fixtures(self):
        for work in Work.objects.all():
            WorkMetrics.create_or_update(work)

    def test_basics(self):
        work = Work.objects.get(pk=1)
        metrics = WorkMetrics.create_or_update(work)

        self.assertEqual(metrics.n_languages, 1)
        self.assertEqual(metrics.n_points_in_time, 1)
        self.assertEqual(metrics.n_expressions, 1)
        self.assertEqual(metrics.n_expected_expressions, 1)

    def test_update(self):
        work = Work.objects.get(pk=1)
        metrics = WorkMetrics.create_or_update(work)

        metrics.n_languages = 99
        metrics.save()

        metrics = WorkMetrics.create_or_update(work)
        metrics.refresh_from_db()
        self.assertEqual(metrics.n_languages, 1)
