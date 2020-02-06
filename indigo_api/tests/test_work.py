# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.core.exceptions import ValidationError

from indigo_api.models import Document, Work, Country


class WorkTestCase(TestCase):
    fixtures = ['countries', 'user', 'taxonomies', 'work', 'published', 'drafts', 'commencements']

    def setUp(self):
        self.work = Work.objects.get(id=1)

    def test_cascade_frbr_uri_changes(self):
        document = Document.objects.get(pk=20)
        self.assertEqual(document.frbr_uri, '/za/act/1945/1')

        document.work.frbr_uri = '/za/act/2999/1'
        document.work.save()

        document = Document.objects.get(pk=20)
        self.assertEqual(document.frbr_uri, '/za/act/2999/1')

    def test_commencement_as_pit_date(self):
        """ When the publication date is unknown, fall back
        to the commencement date as a possible point in time.
        """
        self.work.publication_date = None
        events = self.work.amendments_with_initial_and_arbitrary()
        initial = events[-1]
        self.assertTrue(initial.initial)
        self.assertEqual(initial.date, self.work.commencement_date)

    def test_validates_uri(self):
        country = Country.objects.first()

        work = Work(frbr_uri='bad', country=country)
        self.assertRaises(ValidationError, work.full_clean)

        work = Work(frbr_uri='', country=country)
        self.assertRaises(ValidationError, work.full_clean)
