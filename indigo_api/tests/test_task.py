from collections import defaultdict
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django_fsm import has_transition_perm

from indigo.tasks import TaskBroker
from indigo_api.models import Amendment, Task, Work, Country


class TaskTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomy_topics', 'work', 'drafts']

    def setUp(self):
        self.na = Country.objects.get(country__pk='NA')
        self.za = Country.objects.get(country__pk='ZA')
        self.user = User.objects.get(pk=1)
        self.task = Task(
            title='foo',
            description='bar',
            created_by_user=self.user)

    def setup_blocked_tasks(self):
        self.blocked_task = Task.objects.create(
            title="Blocked task",
            description="Test description",
            country_id=1,
            created_by_user_id=1,
        )
        self.blocking_task = Task.objects.create(
            title="Blocking task",
            description="Test description",
            country_id=1,
            created_by_user_id=1,
        )
        self.blocked_task.blocked_by.add(self.blocking_task)
        self.assertTrue(has_transition_perm(self.blocked_task.block, self.user))
        self.blocked_task.block(self.user)
        self.blocked_task.save()
        self.assertEqual(Task.BLOCKED, self.blocked_task.state)
        self.assertEqual([self.blocking_task], list(self.blocked_task.blocked_by.all()))
        self.assertFalse(has_transition_perm(self.blocked_task.block, self.user))

    def assert_still_blocked_but_by_nothing(self):
        # task is still blocked, but no longer blocked by anything
        self.blocked_task.refresh_from_db()
        self.assertEqual(Task.BLOCKED, self.blocked_task.state)
        self.assertEqual([], list(self.blocked_task.blocked_by.all()))

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
        # the user has permission, and the task is in the right state to be cancelled
        self.assertTrue(has_transition_perm(self.task.cancel, self.user))
        self.task.cancel(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.CANCELLED, self.task.state)
        self.assertIsNotNone(self.task.closed_at)
        self.assertIsNone(self.task.reviewed_by_user)
        # the user still has the permission, but the task itself cannot be re-cancelled
        self.assertFalse(has_transition_perm(self.task.cancel, self.user))

    def test_reopen(self):
        self.task.country = self.za
        self.task.cancel(self.user)
        self.task.save()
        self.task.refresh_from_db()
        self.assertTrue(has_transition_perm(self.task.reopen, self.user))
        self.task.reopen(self.user)

        self.assertEqual(Task.OPEN, self.task.state)
        self.assertIsNone(self.task.closed_at)
        self.assertIsNone(self.task.reviewed_by_user)
        self.assertFalse(has_transition_perm(self.task.reopen, self.user))

    def test_close(self):
        self.task.state = Task.PENDING_REVIEW
        self.task.country = self.za
        self.assertTrue(has_transition_perm(self.task.close, self.user))
        self.task.close(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.DONE, self.task.state)
        self.assertIsNotNone(self.task.closed_at)
        self.assertEqual(self.user, self.task.reviewed_by_user)
        self.assertFalse(has_transition_perm(self.task.close, self.user))

    def test_block(self):
        self.task.state = Task.OPEN
        self.task.country = self.za
        self.task.assign_to(User.objects.get(pk=1), self.user)
        self.assertTrue(has_transition_perm(self.task.block, self.user))
        self.task.block(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.BLOCKED, self.task.state)
        self.assertIsNone(self.task.assigned_to)
        self.assertFalse(has_transition_perm(self.task.block, self.user))

    def test_unblock(self):
        self.task.state = Task.BLOCKED
        self.task.country = self.za
        self.task.save()
        self.assertTrue(has_transition_perm(self.task.unblock, self.user))
        self.task.unblock(self.user)
        self.task.save()
        self.task.refresh_from_db()

        self.assertEqual(Task.OPEN, self.task.state)
        self.assertFalse(has_transition_perm(self.task.unblock, self.user))

    def test_update_blocked_tasks(self):
        self.setup_blocked_tasks()
        # update_blocked_tasks() is called from cancel(), close(), and finish()
        self.blocking_task.update_blocked_tasks(self.blocking_task, self.user)
        self.assert_still_blocked_but_by_nothing()

    def test_update_blocked_tasks_unblock(self):
        self.setup_blocked_tasks()
        # extra setup: a conversion task blocking an import task
        self.blocking_task.code = 'convert-document'
        self.blocking_task.save()
        self.blocked_task.code = 'import-content'
        self.blocked_task.save()
        # update_blocked_tasks() is called from cancel(), close(), and finish()
        self.blocking_task.update_blocked_tasks(self.blocking_task, self.user)

        # task has been unblocked
        self.blocked_task.refresh_from_db()
        self.assertEqual(Task.OPEN, self.blocked_task.state)
        self.assertEqual([], list(self.blocked_task.blocked_by.all()))

    def test_update_blocked_tasks_cancelled(self):
        self.setup_blocked_tasks()
        # extra setup: a conversion task blocking an import task, BUT the import task is cancelled
        self.blocking_task.code = 'convert-document'
        self.blocking_task.save()
        self.blocked_task.code = 'import-content'
        self.blocked_task.state = Task.CANCELLED
        self.blocked_task.save()
        # update_blocked_tasks() is called from cancel(), close(), and finish()
        self.blocking_task.update_blocked_tasks(self.blocking_task, self.user)

        # task can't be unblocked, because it's cancelled, but it's no longer blocked by anything
        self.blocked_task.refresh_from_db()
        self.assertEqual(Task.CANCELLED, self.blocked_task.state)
        self.assertEqual([], list(self.blocked_task.blocked_by.all()))

    def test_update_blocked_tasks_from_cancel(self):
        self.setup_blocked_tasks()
        # cancel() includes a call to update_blocked_tasks()
        self.assertTrue(has_transition_perm(self.blocking_task.cancel, self.user))
        self.blocking_task.cancel(self.user)
        self.assert_still_blocked_but_by_nothing()

    def test_update_blocked_tasks_from_close(self):
        self.setup_blocked_tasks()
        self.blocking_task.state = Task.PENDING_REVIEW
        # close() includes a call to update_blocked_tasks()
        self.assertTrue(has_transition_perm(self.blocking_task.close, self.user))
        self.blocking_task.close(self.user)
        self.assert_still_blocked_but_by_nothing()

    def test_update_blocked_tasks_from_finish(self):
        self.setup_blocked_tasks()
        # finish() includes a call to update_blocked_tasks()
        self.assertTrue(has_transition_perm(self.blocking_task.finish, self.user))
        self.blocking_task.finish(self.user)
        self.assert_still_blocked_but_by_nothing()


class TaskBrokerTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomy_topics', 'work', 'drafts']

    def setUp(self):
        self.broker = TaskBroker(Work.objects.none())
        self.user = User.objects.get(pk=1)

    def test_block_or_cancel_tasks(self):
        blocked_task = Task(state=Task.BLOCKED, country_id=1, created_by_user_id=1)
        self.assertFalse(has_transition_perm(blocked_task.block, self.user))
        self.broker.block_or_cancel_tasks([blocked_task], 'block', self.user)
        self.assertEqual(Task.BLOCKED, blocked_task.state)
        self.assertTrue(has_transition_perm(blocked_task.cancel, self.user))
        self.broker.block_or_cancel_tasks([blocked_task], 'cancel', self.user)
        self.assertEqual(Task.CANCELLED, blocked_task.state)
        self.assertFalse(has_transition_perm(blocked_task.cancel, self.user))
        self.broker.block_or_cancel_tasks([blocked_task], 'cancel', self.user)
        self.assertEqual(Task.CANCELLED, blocked_task.state)

    def test_create_amendment_tasks(self):
        country = Country.objects.get(country__pk='ZA')
        amended_work = Work.objects.create(
            frbr_uri='/akn/za/act/2024/1',
            title='Amended Act, 2024',
            country=country,
            principal=True,
            created_by_user=self.user,
            updated_by_user=self.user,
        )
        amending_work = Work.objects.create(
            frbr_uri='/akn/za/act/2024/2',
            title='Amending Act, 2024',
            country=country,
            principal=False,
            created_by_user=self.user,
            updated_by_user=self.user,
        )
        amendment = Amendment.objects.create(
            amended_work=amended_work,
            amending_work=amending_work,
            date=date(2024, 6, 1),
            created_by_user=self.user,
            updated_by_user=self.user,
        )

        broker = TaskBroker(Work.objects.filter(pk__in=[amended_work.pk, amending_work.pk]))
        data = {
            'conversion_task_description': Task.DESCRIPTIONS['convert-document'],
            'import_task_description': Task.DESCRIPTIONS['import-content'],
            'gazette_task_description': Task.DESCRIPTIONS['link-gazette'],
            'amendment_task_description': Task.DESCRIPTIONS['amendment-instruction'],
            f'amendment_task_description_{amendment.pk}': 'Apply the amendment on the given date.',
            f'amendment_task_create_{amendment.pk}': True,
        }

        broker.create_tasks(self.user, data)

        self.assertEqual(1, len(broker.amendment_instruction_tasks))
        self.assertEqual(1, len(broker.amendment_tasks))

        instruction_task = broker.amendment_instruction_tasks[0]
        amendment_task = broker.amendment_tasks[0]

        self.assertEqual('amendment-instructions', instruction_task.code)
        self.assertEqual('apply-amendment', amendment_task.code)
        self.assertEqual(amended_work, instruction_task.work)
        self.assertEqual(amended_work, amendment_task.work)
        self.assertEqual(amendment.date, instruction_task.timeline_date)
        self.assertEqual(amendment.date, amendment_task.timeline_date)
        self.assertEqual(data['amendment_task_description'], instruction_task.description)
        self.assertEqual(data[f'amendment_task_description_{amendment.pk}'], amendment_task.description)

        self.assertEqual(Task.OPEN, instruction_task.state)
        self.assertEqual(Task.BLOCKED, amendment_task.state)
        self.assertEqual([], list(instruction_task.blocked_by.all()))
        self.assertEqual([instruction_task], list(amendment_task.blocked_by.all()))
        self.assertEqual([amendment_task], list(instruction_task.blocking.all()))
