# -*- coding: utf-8 -*-
from django.test import TestCase
from django.contrib.auth.models import User

from indigo_api.models import Task, Work, Country


class TaskTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work', 'drafts']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.task = Task(
            title='foo',
            description='bar',
            created_by_user=self.user)

    def test_discard_bad_work_country(self):
        na = Country.objects.get(country__pk='NA')

        self.task.country = na
        self.task.work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        self.task.clean()

        self.assertEqual(self.task.country, na)
        self.assertIsNone(self.task.work)

    def test_discard_bad_work_locality(self):
        za = Country.objects.get(country__pk='ZA')
        loc = za.localities.all()[0]

        self.task.country = za
        self.task.locality = loc
        self.task.work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        self.task.clean()

        self.assertEqual(self.task.country, za)
        self.assertEqual(self.task.locality, loc)
        self.assertIsNone(self.task.work)

    def test_cancel(self):
        za = Country.objects.get(country__pk='ZA')
        self.task.country = za
        self.task.cancel(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.CANCELLED, self.task.state)
        self.assertIsNotNone(self.task.closed_at)
        self.assertIsNone(self.task.reviewed_by_user)

    def test_reopen(self):
        za = Country.objects.get(country__pk='ZA')
        self.task.country = za
        self.task.cancel(self.user)
        self.task.save()
        self.task.refresh_from_db()
        self.task.reopen(self.user)

        self.assertEqual(Task.OPEN, self.task.state)
        self.assertIsNone(self.task.closed_at)
        self.assertIsNone(self.task.reviewed_by_user)

    def test_close(self):
        za = Country.objects.get(country__pk='ZA')
        self.task.state = Task.PENDING_REVIEW
        self.task.country = za
        self.task.close(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.DONE, self.task.state)
        self.assertIsNotNone(self.task.closed_at)
        self.assertEqual(self.user, self.task.reviewed_by_user)
