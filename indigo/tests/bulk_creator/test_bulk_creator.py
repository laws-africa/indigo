# -*- coding: utf-8 -*-
import csv
import io
import os
import datetime

from django.test import testcases

from indigo.bulk_creator import SpreadsheetRow
from indigo.plugins import plugins
from indigo_api.models import Country, Work
from indigo_app.models import User


class BulkCreateWorksTest(testcases.TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work']

    def setUp(self):
        self.maxDiff = None
        creator = plugins.for_locale('bulk-creator', 'za', None, None)
        creator.country = Country.objects.get(pk=1)
        creator.locality = None
        creator.user = User.objects.get(pk=1)
        creator.testing = True
        self.creator = creator

    def get_works(self, dry_run, filename):
        file = os.path.join(os.path.dirname(__file__), filename)
        with open(file) as csv_file:
            content = csv_file.read()
            reader = csv.reader(io.StringIO(content))
            table = list(reader)
            return self.creator.create_works(table, dry_run, None)

    def test_basic_preview(self):
        works = self.get_works(True, 'basic.csv')
        self.assertEqual(2, len(works))

        row1 = works[0]
        self.assertEqual('success', row1.status)
        self.assertEqual('Testy 1', row1.work.title)
        self.assertEqual('1', row1.work.number)
        self.assertEqual('2020', row1.work.year)
        self.assertEqual(datetime.date(2020, 1, 1), row1.work.publication_date)
        self.assertFalse(row1.work.stub)
        self.assertFalse(row1.work.commenced)
        self.assertEqual(['Uncommenced'], row1.notes)
        self.assertEqual([], row1.relationships)
        self.assertEqual(['link gazette', 'import content'], row1.tasks)

        row2 = works[1]
        self.assertEqual('success', row2.status)
        self.assertEqual('Testy 2', row2.work.title)
        self.assertEqual('2', row2.work.number)
        self.assertEqual('2020', row2.work.year)
        self.assertEqual(datetime.date(2020, 6, 1), row2.work.publication_date)
        self.assertTrue(row2.work.stub)
        self.assertEqual(['Uncommenced'], row2.notes)
        self.assertEqual([], row2.relationships)
        self.assertEqual(['link gazette'], row2.tasks)

        # not actually created though
        with self.assertRaises(Work.DoesNotExist):
            Work.objects.get(frbr_uri='/akn/za/act/2020/1')
        with self.assertRaises(Work.DoesNotExist):
            Work.objects.get(frbr_uri='/akn/za/act/2020/2')

    def test_basic_live(self):
        works = self.get_works(False, 'basic.csv')
        self.assertEqual(2, len(works))

        work1 = Work.objects.get(frbr_uri='/akn/za/act/2020/1')
        row1 = works[0]
        self.assertEqual(work1, row1.work)
        self.assertEqual('Testy 1', work1.title)
        self.assertEqual('1', work1.number)
        self.assertEqual('2020', work1.year)
        self.assertEqual(datetime.date(2020, 1, 1), work1.publication_date)
        self.assertFalse(work1.stub)
        # no 'notes' when not in preview
        self.assertEqual([], row1.notes)
        self.assertEqual([], row1.relationships)
        tasks = work1.tasks.all()
        self.assertEqual(2, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Import content', task_titles)

        work2 = Work.objects.get(frbr_uri='/akn/za/act/2020/2')
        row2 = works[1]
        self.assertEqual(work2, row2.work)
        self.assertEqual('Testy 2', work2.title)
        self.assertEqual('2', work2.number)
        self.assertEqual('2020', work2.year)
        self.assertEqual(datetime.date(2020, 6, 1), work2.publication_date)
        self.assertTrue(work2.stub)
        # no 'notes' when not in preview
        self.assertEqual([], row2.notes)
        self.assertEqual([], row2.relationships)
        tasks = work2.tasks.all()
        self.assertEqual(1, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)

    def test_errors(self):
        # preview
        works = self.get_works(True, 'errors.csv')
        self.assertEqual(2, len(works))

        row1 = works[0]
        self.assertIsNone(row1.status)
        self.assertEqual('''{"country": [{"message": "This field is required.", "code": "required"}], "locality": [{"message": "Select a valid choice. xyz is not one of the available choices.", "code": "invalid_choice"}], "number": [{"message": "This field is required.", "code": "required"}], "year": [{"message": "Must be a year (yyyy).", "code": "invalid"}], "publication_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}], "assent_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}]}''',
                         row1.errors.as_json())

        row2 = works[1]
        self.assertEqual('success', row2.status)
        self.assertEqual({}, row2.errors)

        # live
        works = self.get_works(False, 'errors.csv')
        row1 = works[0]
        with self.assertRaises(AttributeError):
            row1.work
        self.assertIsNone(row1.status)
        self.assertEqual('''{"country": [{"message": "This field is required.", "code": "required"}], "locality": [{"message": "Select a valid choice. xyz is not one of the available choices.", "code": "invalid_choice"}], "number": [{"message": "This field is required.", "code": "required"}], "year": [{"message": "Must be a year (yyyy).", "code": "invalid"}], "publication_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}], "assent_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}]}''',
                         row1.errors.as_json())

        row2 = works[1]
        work2 = Work.objects.get(frbr_uri='/akn/za/act/2020/2')
        self.assertEqual(work2, row2.work)
        self.assertEqual('success', row2.status)
        self.assertEqual({}, row2.errors)

    def test_get_frbr_uri(self):
        row = SpreadsheetRow
        # not enough details
        with self.assertRaises(AttributeError):
            self.creator.get_frbr_uri(row)

        # add details
        row.country = 'za'
        row.doctype = 'act'
        row.year = '2020'
        row.number = '27'
        row.actor = 'Edith'
        # still not enough
        with self.assertRaises(AttributeError):
            self.creator.get_frbr_uri(row)

        # add empty details
        row.locality = ''
        row.subtype = ''
        uri = self.creator.get_frbr_uri(row)
        # no actor included when there's no subtype
        self.assertEqual('/akn/za/act/2020/27', uri)
        row.subtype = 'GN'
        uri = self.creator.get_frbr_uri(row)
        # now both subtype and actor are included
        self.assertEqual('/akn/za/act/gn/edith/2020/27', uri)

    def test_find_work(self):
        self.creator.works = []
        # live
        self.creator.dry_run = False
        given_string = "Constitution of the Republic of South Africa, 1996"
        work = self.creator.find_work(given_string)
        self.assertEqual(10, work.id)

        given_string = "I don't exist"
        work = self.creator.find_work(given_string)
        self.assertIsNone(work)

        # also get real work when previewing
        self.creator.dry_run = True
        given_string = "Constitution of the Republic of South Africa, 1996"
        work = self.creator.find_work(given_string)
        self.assertEqual(10, work.id)

        given_string = "I don't exist"
        work = self.creator.find_work(given_string)
        self.assertIsNone(work)

        row = SpreadsheetRow
        row.work = Work(title="I'm being imported in the same batch")
        self.creator.works.append(row)
        given_string = "I'm being imported in the same batch"
        work = self.creator.find_work(given_string)
        self.assertEqual("I'm being imported in the same batch (about to be imported)", work)

        row = SpreadsheetRow
        row.work = Work(frbr_uri='/akn/za/act/2020/1')
        self.creator.works.append(row)
        given_string = "/akn/za/act/2020/1 - I'm being imported in the same batch"
        work = self.creator.find_work(given_string)
        self.assertEqual("/akn/za/act/2020/1 - I'm being imported in the same batch (about to be imported)", work)

    def test_link_parents(self):
        # preview
        works = self.get_works(True, 'parents.csv')
        row2 = works[1]
        self.assertEqual(['Subleg under /akn/za/act/2020/1 – Parent (about to be imported)'], row2.relationships)

        row3 = works[2]
        self.assertEqual(['link gazette', 'import content', 'link primary work'], row3.tasks)

        # live
        works = self.get_works(False, 'parents.csv')
        parent = works[0].work
        child = works[1].work
        lonely_child = works[2].work
        self.assertEqual(parent, child.parent_work)
        self.assertIsNone(lonely_child.parent_work)
        task_titles = [t.title for t in lonely_child.tasks.all()]
        self.assertIn('Link primary work', task_titles)

    def test_link_children(self):
        works = self.get_works(True, 'children.csv')
        row1 = works[0]
        self.assertEqual([
            'Main work of /akn/za/act/2020/2 (about to be imported)',
            'Main work of /akn/za/act/2020/3 (about to be imported)'],
            row1.relationships)

        works = self.get_works(False, 'children.csv')
        parent = works[0].work
        child1 = works[1].work
        child2 = works[2].work
        self.assertEqual(parent, child1.parent_work)
        self.assertEqual(parent, child2.parent_work)

        # the children already have a parent work
        works = self.get_works(False, 'children_2.csv')
        tasks1 = [t.title for t in child1.tasks.all()]
        tasks2 = [t.title for t in child2.tasks.all()]
        self.assertEqual(parent, child1.parent_work)
        self.assertEqual(parent, child2.parent_work)
        self.assertIn('Update subleg?', tasks1)
        self.assertIn('Update subleg?', tasks2)

    def test_link_commencements_passive(self):
        # preview (commencement objects aren't created)
        works = self.get_works(True, 'commencements_passive.csv')
        uncommenced = works[0]
        both = works[1]
        date_only = works[2]
        commenced_by_only = works[3]
        commencement_notice = works[4]
        error = works[5]

        # uncommenced
        self.assertEqual(['Uncommenced'], uncommenced.notes)
        self.assertEqual([], uncommenced.relationships)
        self.assertEqual(['link gazette', 'import content'], uncommenced.tasks)

        # both
        self.assertEqual([], both.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/5 - '
                          'Commencement notice 1 (about to be imported) '
                          'on 2020-06-05'],
                         both.relationships)
        self.assertEqual(['link gazette', 'import content'], both.tasks)

        # date only
        self.assertEqual([], date_only.notes)
        self.assertEqual([], date_only.relationships)
        self.assertEqual(['link gazette', 'import content'], date_only.tasks)

        # commenced_by only
        self.assertEqual([], commenced_by_only.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/5 - '
                          'Commencement notice 1 (about to be imported) '
                          'on (unknown)'],
                         commenced_by_only.relationships)
        self.assertEqual(['link gazette', 'import content'], commenced_by_only.tasks)

        # commencement notice
        self.assertEqual([], commencement_notice.notes)
        self.assertEqual([], commencement_notice.relationships)
        self.assertEqual(['link gazette'], commencement_notice.tasks)

        # error
        self.assertEqual([], error.notes)
        self.assertEqual([], error.relationships)
        self.assertEqual(['link gazette', 'import content', 'link commencement'], error.tasks)

        # live
        works = self.get_works(False, 'commencements_passive.csv')
        uncommenced = works[0]
        both = works[1]
        date_only = works[2]
        commenced_by_only = works[3]
        commencement_notice = works[4]
        error = works[5]

        # uncommenced
        self.assertFalse(uncommenced.work.commenced)
        self.assertIsNone(uncommenced.work.commencement_date)
        self.assertIsNone(uncommenced.work.commencing_work)
        self.assertEqual([], uncommenced.notes)
        self.assertEqual([], uncommenced.relationships)
        tasks = uncommenced.work.tasks.all()
        self.assertEqual(2, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Import content', task_titles)

        # both
        self.assertTrue(both.work.commenced)
        self.assertEqual(datetime.date(2020, 6, 5),
                         both.work.commencement_date)
        self.assertEqual(commencement_notice.work, both.work.commencing_work)
        self.assertEqual([], both.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/5 (Commencement notice 1) on 2020-06-05'],
                         both.relationships)
        tasks = both.work.tasks.all()
        self.assertEqual(2, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Import content', task_titles)

        # date only
        self.assertTrue(date_only.work.commenced)
        self.assertEqual(datetime.date(2020, 6, 5),
                         date_only.work.commencement_date)
        self.assertIsNone(date_only.work.commencing_work)
        self.assertEqual([], date_only.notes)
        self.assertEqual([], date_only.relationships)
        tasks = date_only.work.tasks.all()
        self.assertEqual(2, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Import content', task_titles)

        # commenced_by only
        self.assertTrue(commenced_by_only.work.commenced)
        self.assertIsNone(commenced_by_only.work.commencement_date)
        self.assertEqual(commencement_notice.work,
                         commenced_by_only.work.commencing_work)
        self.assertEqual([], both.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/5 (Commencement notice 1) on (unknown)'], commenced_by_only.relationships)
        tasks = commenced_by_only.work.tasks.all()
        self.assertEqual(2, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Import content', task_titles)

        # commencement notice
        self.assertTrue(commencement_notice.work.commenced)
        self.assertEqual(datetime.date(2020, 7, 1),
                         commencement_notice.work.commencement_date)
        self.assertIsNone(commencement_notice.work.commencing_work)
        self.assertEqual([], commencement_notice.notes)
        self.assertEqual([], commencement_notice.relationships)
        tasks = commencement_notice.work.tasks.all()
        self.assertEqual(1, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)

        # error
        self.assertFalse(error.work.commenced)
        self.assertIsNone(error.work.commencement_date)
        self.assertIsNone(error.work.commencing_work)
        self.assertEqual([], error.notes)
        self.assertEqual([], error.relationships)
        tasks = error.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Import content', task_titles)
        self.assertIn('Link commencement', task_titles)

        # commenced later, preview
        works = self.get_works(True, 'commencements_passive_later.csv')
        now_commenced = works[0]
        self.assertEqual('duplicate', now_commenced.status)
        self.assertTrue(now_commenced.commenced)
        self.assertEqual(datetime.date(2020, 9, 1), now_commenced.commencement_date)
        self.assertIsNotNone(now_commenced.commenced_by)
        # but commencement object doesn't exist yet
        self.assertIsNone(now_commenced.work.commencement_date)
        self.assertEqual([], now_commenced.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/7 - '
                          'Commencement notice 2 (about to be imported) '
                          'on 2020-09-01'],
                         now_commenced.relationships)
        self.assertEqual([], now_commenced.tasks)

        # commenced later, live
        works = self.get_works(False, 'commencements_passive_later.csv')
        now_commenced = works[0]
        actual = Work.objects.get(frbr_uri=now_commenced.work.frbr_uri)
        commencement_notice2 = works[1]
        self.assertEqual('duplicate', now_commenced.status)
        self.assertEqual(uncommenced.work, now_commenced.work)
        self.assertEqual(actual, now_commenced.work)
        self.assertTrue(actual.commenced)
        self.assertEqual(datetime.date(2020, 9, 1),
                         actual.commencement_date)
        self.assertEqual(commencement_notice2.work, actual.commencing_work)
        self.assertEqual([], now_commenced.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/7 (Commencement notice 2) on 2020-09-01'],
                         now_commenced.relationships)
        tasks = actual.tasks.all()
        self.assertEqual(2, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Import content', task_titles)

    def test_link_amendments_active(self):
        # preview
        works = self.get_works(True, 'amendments_active.csv')
        main = works[0]
        amend1 = works[1]
        amend2 = works[2]
        error = works[3]
        self.assertEqual('success', main.status)
        self.assertEqual('success', amend1.status)
        self.assertEqual('success', amend2.status)
        self.assertEqual('success', error.status)

        self.assertEqual([], main.notes)
        self.assertEqual([], main.relationships)
        self.assertEqual(['link gazette', 'import content'], main.tasks)

        self.assertEqual(
            ["An 'Apply amendment' task will be created on /akn/za/act/2020/1 – Main (about to be imported)"],
            amend1.notes)
        self.assertEqual(['Amends /akn/za/act/2020/1 – Main (about to be imported)'], amend1.relationships)
        self.assertEqual(['link gazette'], amend1.tasks)

        self.assertEqual(
            ["An 'Apply amendment' task will be created on /akn/za/act/2020/1 – Main (about to be imported)"],
            amend2.notes)
        self.assertEqual(['Amends /akn/za/act/2020/1 – Main (about to be imported)'], amend2.relationships)
        self.assertEqual(['link gazette'], amend2.tasks)

        self.assertEqual([], error.notes)
        self.assertEqual([], error.relationships)
        self.assertEqual(['link gazette', 'link amendment'], error.tasks)

        # live
        works = self.get_works(False, 'amendments_active.csv')
        main = works[0].work
        amend1 = works[1].work
        amend2 = works[2].work
        error = works[3].work

        amendments = main.amendments.all()
        self.assertEqual(2, len(amendments))
        amenders = [a.amending_work for a in amendments]
        self.assertIn(amend1, amenders)
        self.assertIn(amend2, amenders)

        main_tasks = [t.title for t in main.tasks.all()]
        self.assertEqual(2, main_tasks.count('Apply amendment'))

        error_tasks = [t.title for t in error.tasks.all()]
        self.assertIn('Link amendment', error_tasks)

    def test_link_amendments_passive(self):
        # preview
        works = self.get_works(True, 'amendments_passive.csv')
        main = works[0]
        dupe1 = works[1]
        dupe2 = works[2]
        dupe3 = works[3]
        amend_1 = works[4]
        amend_2 = works[5]
        amend_3 = works[5]
        self.assertEqual('success', main.status)
        self.assertEqual('success', dupe1.status)
        self.assertEqual('success', dupe2.status)
        self.assertEqual('success', dupe3.status)
        self.assertEqual('success', amend_1.status)
        self.assertEqual('success', amend_2.status)
        self.assertEqual('success', amend_3.status)
        self.assertEqual(['Duplicate in batch', "An 'Apply amendment' task will be created on this work"], main.notes)
        self.assertEqual(['Duplicate in batch', "An 'Apply amendment' task will be created on this work"], dupe1.notes)
        self.assertEqual(['Duplicate in batch', "An 'Apply amendment' task will be created on this work"], dupe2.notes)
        self.assertEqual(['Duplicate in batch'], dupe3.notes)
        self.assertEqual([], amend_1.notes)
        self.assertEqual([], amend_2.notes)
        self.assertEqual([], amend_3.notes)
        self.assertEqual(['Amended by /akn/za/act/2020/2 – First (about to be imported)'], main.relationships)
        self.assertEqual(['Amended by /akn/za/act/2020/3 – Second (about to be imported)'], dupe1.relationships)
        self.assertEqual(['Amended by /akn/za/act/2020/4 – Third (about to be imported)'], dupe2.relationships)
        self.assertEqual([], dupe3.relationships)
        self.assertEqual([], amend_1.relationships)
        self.assertEqual([], amend_2.relationships)
        self.assertEqual([], amend_3.relationships)
        self.assertEqual(['link gazette', 'import content'], main.tasks)
        self.assertEqual(['link gazette', 'import content'], dupe1.tasks)
        self.assertEqual(['link gazette', 'import content'], dupe2.tasks)
        self.assertEqual(['link gazette', 'import content', 'link amendment passive'], dupe3.tasks)
        self.assertEqual(['link gazette'], amend_1.tasks)
        self.assertEqual(['link gazette'], amend_2.tasks)
        self.assertEqual(['link gazette'], amend_3.tasks)

        # live
        # works = self.get_works(False, 'amendments_passive.csv')
        # main = works[0].work
        # amend_1 = works[1].work
        # amend_2 = works[2].work
        # error = works[3].work
        # amendments = main.amendments.all()
        # self.assertEqual(2, len(amendments))
        # amenders = [a.amending_work for a in amendments]
        # self.assertIn(amend_1, amenders)
        # self.assertIn(amend_2, amenders)
        # error_tasks = [t.title for t in error.tasks.all()]
        # self.assertIn('Link amendment pending commencement', amend3_tasks)

    def test_link_repeals_passive(self):
        # preview
        works = self.get_works(True, 'repeals_passive.csv')
        main1 = works[0]
        repeal1 = works[1]
        main2 = works[2]
        repeal2 = works[3]
        main3 = works[4]
        self.assertEqual('success', main1.status)
        self.assertEqual('success', repeal1.status)
        self.assertEqual('success', main2.status)
        self.assertEqual('success', repeal2.status)
        self.assertEqual('success', main3.status)

        self.assertEqual([], main1.notes)
        self.assertEqual(['Repealed by /akn/za/act/2020/2 (about to be imported)'], main1.relationships)
        self.assertEqual(['link gazette', 'import content'], main1.tasks)

        self.assertEqual([], main2.notes)
        self.assertEqual(['Repealed by /akn/za/act/2020/4 (about to be imported)'], main2.relationships)
        self.assertEqual(['link gazette', 'import content'], main2.tasks)

        self.assertEqual([], main3.notes)
        self.assertEqual([], main3.relationships)
        self.assertEqual(['link gazette', 'import content', 'no repeal match'], main3.tasks)

        # live
        works = self.get_works(False, 'repeals_passive.csv')
        main1 = works[0].work
        repeal1 = works[1].work
        main2 = works[2].work
        repeal2 = works[3].work
        main3 = works[4].work

        self.assertEqual(main1.repealed_by, repeal1)
        self.assertNotIn('Link repeal', [t.title for t in main1.tasks.all()])
        self.assertIsNone(main2.repealed_by)
        self.assertIn('Link repeal', [t.title for t in repeal2.tasks.all()])
        self.assertIsNone(main3.repealed_by)
        self.assertIn('Link repeal', [t.title for t in main3.tasks.all()])

    def test_duplicates(self):
        # preview
        works = self.get_works(True, 'duplicates.csv')
        work1 = works[0]
        work2 = works[1]
        self.assertEqual('success', work1.status)
        self.assertEqual('success', work2.status)
        self.assertEqual(['Duplicate in batch'], work1.notes)
        self.assertEqual(['Uncommenced', 'Duplicate in batch'], work2.notes)

        # live
        works = self.get_works(False, 'duplicates.csv')
        work1 = works[0]
        work2 = works[1]
        self.assertEqual('success', work1.status)
        self.assertEqual('duplicate', work2.status)
        self.assertEqual(work2.work, work1.work)
        self.assertEqual('Testy 1', work1.work.title)
        self.assertEqual([], work1.notes)
        self.assertEqual([], work2.notes)

    # TODO:
    #  - test_link_commencements_active
    #  - test_link_amendments_passive
    #  - test_link_repeals_active
    #  - test_link_publication_document
    #  - test_link_taxonomy
    #  - test_create_task (include workflow too)
    #  - test_add_extra_properties
    #  - test_aliases: transform_aliases and transform_error_aliases
    #  - test subclasses of BaseBulkCreator, RowValidationFormBase
