from datetime import date

from django.test import TestCase

from indigo.tasks import TaskBroker
from indigo_api.models import Amendment, Task, Work, Country, User


class BaseTaskBrokerTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomy_topics', 'work', 'published']

    def setUp(self):
        self.country = Country.objects.first()
        # exclude any other new works created in fixtures/works.json for other tests
        self.works = Work.objects.exclude(pk=21)
        self.broker = TaskBroker(self.works)
        self.user = User.objects.first()

    def test_init(self):
        broker_works = list(self.broker.works)
        ignored_works = list(self.broker.ignored_works)
        for work in self.works:
            self.assertIn(work, broker_works)
        self.assertEqual([], ignored_works)
        self.assertEqual(list(self.works.filter(principal=True)), list(self.broker.import_task_works))
        self.assertEqual(11, self.broker.import_task_works.count())
        self.assertEqual(18, len(self.broker.gazette_task_works))
        self.assertEqual(8, len(self.broker.amendments))

    def test_create_tasks(self):
        data = {
            'conversion_task_description': 'Convert the input file into a .docx file and remove automatic numbering.',
            'update_conversion_tasks': 'cancel',
            'import_task_description': 'Import the content for this work at the appropriate date — usually the publication or consolidation date.',
            'update_import_tasks': 'cancel',
            'gazette_task_description': 'Find and link the Gazette (original publication document) for this work.',
            'update_gazette_tasks': 'cancel',
            'update_amendment_tasks': 'cancel',
        }
        for amendment in self.broker.amendments:
            data[f'amendment_task_create_{amendment.pk}'] = True
            data[f'amendment_task_description_{amendment.pk}'] = 'Apply the amendments made by %(amending_title)s' \
                                                                 ' (%(numbered_title)s) on the given date.' % {
                                                                     'amending_title': amendment.amending_work.title,
                                                                     'numbered_title': amendment.amending_work.numbered_title(),
                                                                 }
        self.broker.create_tasks(self.user, data=data)
        self.assertEqual(11, len(self.broker.conversion_tasks))
        for task in self.broker.conversion_tasks:
            self.assertEqual('cancelled', task.state)
        self.assertEqual(11, len(self.broker.import_tasks))
        for task in self.broker.import_tasks:
            self.assertEqual('cancelled', task.state)
            self.assertTrue(task.blocked_by.exists())
            self.assertIn(task.blocked_by.first(), self.broker.conversion_tasks)
        self.assertEqual(18, len(self.broker.gazette_tasks))
        for task in self.broker.gazette_tasks:
            self.assertEqual('cancelled', task.state)
        self.assertEqual(8, len(self.broker.amendment_tasks))
        for task in self.broker.amendment_tasks:
            self.assertEqual('cancelled', task.state)

    def test_create_tasks_blocks_new_amendment_task_by_prior_apply_amendment_task(self):
        amended_work = Work.objects.create(
            frbr_uri='/akn/za/act/2024/101',
            title='Amended Act 101',
            country=self.country,
            principal=False,
            created_by_user=self.user,
            updated_by_user=self.user,
        )
        amending_work = Work.objects.create(
            frbr_uri='/akn/za/act/2024/102',
            title='Amending Act 102',
            country=self.country,
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

        prior_amendment_task = Task.objects.create(
            country=amended_work.country,
            locality=amended_work.locality,
            work=amended_work,
            code='apply-amendment',
            title=Task.MAIN_CODES['apply-amendment'],
            timeline_date=date(2024, 5, 1),
            description='Apply earlier amendment.',
            created_by_user=self.user,
            updated_by_user=self.user,
        )

        broker = TaskBroker(Work.objects.filter(pk__in=[amended_work.pk, amending_work.pk]))
        data = {
            'conversion_task_description': Task.DESCRIPTIONS['convert-document'],
            'import_task_description': Task.DESCRIPTIONS['import-content'],
            'gazette_task_description': Task.DESCRIPTIONS['link-gazette'],
            f'amendment_task_description_{amendment.pk}': 'Apply the amendment on the given date.',
            f'amendment_task_create_{amendment.pk}': True,
        }
        broker.create_tasks(self.user, data)

        amendment_task = broker.amendment_tasks[0]
        self.assertIn(prior_amendment_task, amendment_task.blocked_by.all())
        self.assertEqual(1, amendment_task.blocked_by.filter(code='apply-amendment').count())
        self.assertEqual(1, amendment_task.blocked_by.filter(code='amendment-instructions').count())

    def test_create_tasks_processes_amendments_in_ascending_date_order(self):
        amended_work = Work.objects.create(
            frbr_uri='/akn/za/act/2024/201',
            title='Amended Act 201',
            country=self.country,
            principal=False,
            created_by_user=self.user,
            updated_by_user=self.user,
        )
        early_amending_work = Work.objects.create(
            frbr_uri='/akn/za/act/2024/202',
            title='Early Amending Act 202',
            country=self.country,
            principal=False,
            created_by_user=self.user,
            updated_by_user=self.user,
        )
        late_amending_work = Work.objects.create(
            frbr_uri='/akn/za/act/2024/203',
            title='Late Amending Act 203',
            country=self.country,
            principal=False,
            created_by_user=self.user,
            updated_by_user=self.user,
        )
        late_amendment = Amendment.objects.create(
            amended_work=amended_work,
            amending_work=late_amending_work,
            date=date(2024, 8, 1),
            created_by_user=self.user,
            updated_by_user=self.user,
        )
        early_amendment = Amendment.objects.create(
            amended_work=amended_work,
            amending_work=early_amending_work,
            date=date(2024, 6, 1),
            created_by_user=self.user,
            updated_by_user=self.user,
        )

        broker = TaskBroker(Work.objects.filter(pk__in=[amended_work.pk, early_amending_work.pk, late_amending_work.pk]))
        data = {
            'conversion_task_description': Task.DESCRIPTIONS['convert-document'],
            'import_task_description': Task.DESCRIPTIONS['import-content'],
            'gazette_task_description': Task.DESCRIPTIONS['link-gazette'],
            f'amendment_task_description_{early_amendment.pk}': 'Apply early amendment.',
            f'amendment_task_create_{early_amendment.pk}': True,
            f'amendment_task_description_{late_amendment.pk}': 'Apply late amendment.',
            f'amendment_task_create_{late_amendment.pk}': True,
        }
        broker.create_tasks(self.user, data)

        early_task = next(t for t in broker.amendment_tasks if t.timeline_date == date(2024, 6, 1))
        late_task = next(t for t in broker.amendment_tasks if t.timeline_date == date(2024, 8, 1))

        self.assertEqual(0, early_task.blocked_by.filter(code='apply-amendment').count())
        self.assertEqual(1, late_task.blocked_by.filter(code='apply-amendment', timeline_date=date(2024, 6, 1)).count())
