import datetime
from django.test import TestCase

from indigo_api.models import Work, TaxonomyTopic, Country, Commencement, Amendment


class TaxonomyTopicSignalTestCase(TestCase):
    fixtures = ['languages_data', 'countries', 'user']

    def setUp(self):
        # make them related through the parent relationship
        self.repealing_work = Work.objects.create(
            country=Country.objects.get(country__pk='ZA'),
            frbr_uri="/akn/za/act/2010/2",
            title='Repealing work',
        )
        self.repealed_work = Work.objects.create(
            country=Country.objects.get(country__pk='ZA'),
            frbr_uri="/akn/za/act/2005/1",
            title='Principal work',
            principal=True,
            repealed_date=datetime.date(2025, 4, 9),
            repealed_by=self.repealing_work,
        )

        self.topic_with_copy_flag = TaxonomyTopic.add_root(name='Topic with Copy Flag', copy_from_principal=True)
        self.topic_without_copy_flag = TaxonomyTopic.add_root(name='Topic without Copy Flag', copy_from_principal=False)

    def test_add_topic_with_copy_flag(self):
        self.repealed_work.taxonomy_topics.add(self.topic_with_copy_flag)
        self.assertIn(self.topic_with_copy_flag, self.repealed_work.taxonomy_topics.all())
        self.assertIn(self.topic_with_copy_flag, self.repealing_work.taxonomy_topics.all())

    def test_remove_topic_with_copy_flag(self):
        self.repealed_work.taxonomy_topics.add(self.topic_with_copy_flag)
        self.repealed_work.taxonomy_topics.remove(self.topic_with_copy_flag)
        self.assertNotIn(self.topic_with_copy_flag, self.repealed_work.taxonomy_topics.all())
        self.assertNotIn(self.topic_with_copy_flag, self.repealing_work.taxonomy_topics.all())

    def test_add_topic_without_flag(self):
        self.repealed_work.taxonomy_topics.add(self.topic_without_copy_flag)
        self.assertIn(self.topic_without_copy_flag, self.repealed_work.taxonomy_topics.all())
        self.assertNotIn(self.topic_without_copy_flag, self.repealing_work.taxonomy_topics.all())

    def test_remove_topic_without_flag(self):
        self.repealed_work.taxonomy_topics.add(self.topic_without_copy_flag)
        self.repealed_work.taxonomy_topics.remove(self.topic_without_copy_flag)
        self.assertNotIn(self.topic_without_copy_flag, self.repealed_work.taxonomy_topics.all())
        self.assertNotIn(self.topic_without_copy_flag, self.repealing_work.taxonomy_topics.all())

    def test_set_topic_on_work(self):
        self.repealed_work.taxonomy_topics.set([self.topic_with_copy_flag])
        self.assertIn(self.topic_with_copy_flag, self.repealed_work.taxonomy_topics.all())
        self.assertIn(self.topic_with_copy_flag, self.repealing_work.taxonomy_topics.all())

    def test_add_work_to_topic(self):
        self.topic_with_copy_flag.works.add(self.repealed_work)
        self.assertIn(self.topic_with_copy_flag, self.repealed_work.taxonomy_topics.all())
        self.assertIn(self.topic_with_copy_flag, self.repealing_work.taxonomy_topics.all())

    def test_commencement_added(self):
        work = Work.objects.create(
            country=Country.objects.get(country__pk='ZA'),
            frbr_uri="/akn/za/act/2020/1",
            title='Work with commencement',
            principal=True,
        )
        self.topic_with_copy_flag.works.add(work)

        commencing_work = Work.objects.create(
            country=Country.objects.get(country__pk='ZA'),
            frbr_uri="/akn/za/act/2020/2",
            title='Commencing work',
            principal=False,
        )

        Commencement.objects.create(
            commenced_work=work,
            commencing_work=commencing_work,
            date=datetime.date(2020, 4, 9),
        )

        self.assertIn(self.topic_with_copy_flag, commencing_work.taxonomy_topics.all())

    def test_amendment_added(self):
        work = Work.objects.create(
            country=Country.objects.get(country__pk='ZA'),
            frbr_uri="/akn/za/act/2020/1",
            title='Work with amendment',
            principal=True,
        )
        self.topic_with_copy_flag.works.add(work)

        amending_work = Work.objects.create(
            country=Country.objects.get(country__pk='ZA'),
            frbr_uri="/akn/za/act/2020/2",
            title='Amending work',
            principal=False,
        )

        Amendment.objects.create(
            amended_work=work,
            amending_work=amending_work,
            date=datetime.date(2020, 4, 9),
        )

        self.assertIn(self.topic_with_copy_flag, amending_work.taxonomy_topics.all())


