# -*- coding: utf-8 -*-
from django.test import TestCase

from indigo_api.models import Task, Work, Country


class TaskTestCase(TestCase):
    fixtures = ['countries', 'work', 'drafts']

    def setUp(self):
        self.task = Task(title='foo', description='bar')

    def test_discard_bad_work_country(self):
        na = Country.objects.get(country__pk='NA')

        self.task.country = na
        self.task.work = Work.objects.get(frbr_uri='/za/act/2014/10')
        self.task.clean()

        self.assertEqual(self.task.country, na)
        self.assertIsNone(self.task.work)

    def test_discard_bad_work_locality(self):
        za = Country.objects.get(country__pk='ZA')
        loc = za.localities.all()[0]

        self.task.country = za
        self.task.locality = loc
        self.task.work = Work.objects.get(frbr_uri='/za/act/2014/10')
        self.task.clean()

        self.assertEqual(self.task.country, za)
        self.assertEqual(self.task.locality, loc)
        self.assertIsNone(self.task.work)
