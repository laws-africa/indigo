# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError

from indigo_api.models import Document, Work, Country


class WorkTestCase(TestCase):
    fixtures = ['countries', 'user', 'work', 'published', 'drafts']

    def setUp(self):
        self.work = Work.objects.get(id=1)

    def test_cascade_frbr_uri_changes(self):
        document = Document.objects.get(pk=20)
        self.assertEqual(document.frbr_uri, '/za/act/1945/1')

        document.work.frbr_uri = '/za/act/2999/1'
        document.work.save()

        document = Document.objects.get(pk=20)
        self.assertEqual(document.frbr_uri, '/za/act/2999/1')

    def test_validates_uri(self):
        country = Country.objects.first()

        work = Work(frbr_uri='bad', country=country)
        self.assertRaises(ValidationError, work.full_clean)

        work = Work(frbr_uri='', country=country)
        self.assertRaises(ValidationError, work.full_clean)
