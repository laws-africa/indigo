# -*- coding: utf-8 -*-
from django.test import TestCase
from django.contrib.auth.models import User

from indigo_api.models import Task, Work, Country


class TaskTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work', 'drafts']

    def setUp(self):
        self.na = Country.objects.get(country__pk='NA')
        self.za = Country.objects.get(country__pk='ZA')
        self.user = User.objects.get(pk=1)
        self.task = Task(
            title='foo',
            description='bar',
            created_by_user=self.user)

    def test_discard_bad_work_country(self):
        self.task.country = self.na
        self.task.work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        self.task.clean()

        self.assertEqual(self.task.country, self.na)
        self.assertIsNone(self.task.work)

    def test_discard_bad_work_locality(self):
        loc = self.za.localities.all()[0]

        self.task.country = self.za
        self.task.locality = loc
        self.task.work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        self.task.clean()

        self.assertEqual(self.task.country, self.za)
        self.assertEqual(self.task.locality, loc)
        self.assertIsNone(self.task.work)

    def test_cancel(self):
        self.task.country = self.za
        self.task.cancel(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.CANCELLED, self.task.state)
        self.assertIsNotNone(self.task.closed_at)
        self.assertIsNone(self.task.reviewed_by_user)

    def test_reopen(self):
        self.task.country = self.za
        self.task.cancel(self.user)
        self.task.save()
        self.task.refresh_from_db()
        self.task.reopen(self.user)

        self.assertEqual(Task.OPEN, self.task.state)
        self.assertIsNone(self.task.closed_at)
        self.assertIsNone(self.task.reviewed_by_user)

    def test_close(self):
        self.task.state = Task.PENDING_REVIEW
        self.task.country = self.za
        self.task.close(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.DONE, self.task.state)
        self.assertIsNotNone(self.task.closed_at)
        self.assertEqual(self.user, self.task.reviewed_by_user)

    def test_block(self):
        self.task.state = Task.OPEN
        self.task.country = self.za
        self.task.assign_to(User.objects.get(pk=1), self.user)
        self.task.block(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.BLOCKED, self.task.state)
        self.assertIsNone(self.task.assigned_to)

    def test_unblock(self):
        self.task.state = Task.BLOCKED
        self.task.country = self.za
        self.task.unblock(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.OPEN, self.task.state)

    def test_update_blocked_tasks(self):
        blocked_task = Task.objects.create(
            title="Blocked task",
            description="Test description",
            country_id=1,
            created_by_user_id=1,
        )
        blocking_task = Task.objects.create(
            title="Blocking task",
            description="Test description",
            country_id=1,
            created_by_user_id=1,
        )

        blocked_task.blocked_by.add(blocking_task)
        blocked_task.block(self.user)
        blocked_task.save()

        self.assertEqual(Task.BLOCKED, blocked_task.state)
        self.assertEqual([blocking_task], list(blocked_task.blocked_by.all()))

        blocking_task.cancel(self.user)

        # task is still blocked, but no longer blocked by anything
        self.assertEqual(Task.BLOCKED, blocked_task.state)
        self.assertEqual([], list(blocked_task.blocked_by.all()))
