from django.test import TestCase

from indigo.tasks import TaskBroker
from indigo_api.models import Work, Country, User


class BaseTaskBrokerTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'taxonomy_topics', 'work', 'published']

    def setUp(self):
        self.country = Country.objects.first()
        self.works = Work.objects.all()
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
            data[f'amendment_task_description_{amendment.pk}'] = 'Apply the amendments made by %(amending_title)s' \
                                                                 ' (%(numbered_title)s) on %(date)s.' % {
                                                                     'amending_title': amendment.amending_work.title,
                                                                     'numbered_title': amendment.amending_work.numbered_title(),
                                                                     'date': amendment.date,
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
