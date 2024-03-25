import csv
import io
import os
import datetime

from django.conf import settings
from django.test import testcases

from indigo.bulk_creator import SpreadsheetRow, BaseBulkCreator
from indigo_api.models import Country, Work, TaxonomyTopic, Locality
from indigo_app.models import User


class BaseBulkCreatorTest(testcases.TestCase):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomy_topics', 'work', 'subtype']

    def setUp(self):
        self.maxDiff = None
        creator = BaseBulkCreator()
        creator.country = Country.objects.get(pk=1)
        creator.locality = None
        creator.user = User.objects.get(pk=1)
        creator.testing = True
        settings.INDIGO['EXTRA_DOCTYPES']['za'] = [('Document', 'doc'), ('Report', 'debateReport'), ('Statement', 'statement')]
        self.creator = creator

    def get_works(self, dry_run, filename, form_data=None):
        form_data = form_data or {}
        file = os.path.join(os.path.dirname(__file__), filename)
        with open(file) as csv_file:
            content = csv_file.read()
            reader = csv.reader(io.StringIO(content))
            table = list(reader)
            return self.creator.create_works(table, dry_run, form_data)

    def test_basic_preview(self):
        works = self.get_works(True, 'basic.csv')
        self.assertEqual(5, len(works))

        row1 = works[0]
        self.assertEqual('success', row1.status)
        self.assertEqual('Testy 1', row1.work.title)
        self.assertEqual('1', row1.work.number)
        self.assertEqual('2020', row1.work.year)
        self.assertEqual(datetime.date(2020, 1, 1), row1.work.publication_date)
        self.assertFalse(row1.work.stub)
        self.assertTrue(row1.work.principal)
        self.assertFalse(row1.work.commenced)
        self.assertEqual(['Uncommenced', 'Principal work'], row1.notes)
        self.assertEqual([], row1.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], row1.tasks)

        row2 = works[1]
        self.assertEqual('success', row2.status)
        self.assertEqual('Testy 2', row2.work.title)
        self.assertEqual('2', row2.work.number)
        self.assertEqual('2020', row2.work.year)
        self.assertEqual(datetime.date(2020, 6, 1), row2.work.publication_date)
        self.assertTrue(row2.work.stub)
        self.assertFalse(row2.work.principal)
        self.assertEqual(['Uncommenced', 'Stub'], row2.notes)
        self.assertEqual([], row2.relationships)
        self.assertEqual(['link gazette'], row2.tasks)

        row3 = works[2]
        self.assertEqual('success', row3.status)
        self.assertEqual('Testy 3', row3.work.title)
        self.assertEqual('debatereport', row3.work.nature)
        self.assertEqual('et-à-l-information-financière', row3.work.number)
        self.assertEqual('2020', row3.work.year)
        self.assertEqual(datetime.date(2020, 6, 1), row3.work.publication_date)
        self.assertFalse(row3.work.stub)
        self.assertTrue(row3.work.principal)
        self.assertEqual(['Uncommenced', 'Principal work'], row3.notes)
        self.assertEqual([], row3.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], row3.tasks)

        # work with commencement_date set to '9999-01-01' is imported as 
        # commenced but without a commencement_date
        row4 = works[3]
        self.assertEqual('success', row4.status)
        self.assertEqual('Unknown commencement date', row4.work.title)
        self.assertEqual('act', row4.work.nature)
        self.assertEqual('64', row4.work.number)
        self.assertEqual('2013', row4.work.year)
        self.assertEqual(datetime.date(2013, 10, 21), row4.work.publication_date)
        self.assertEqual(None, row4.work.commencement_date)
        self.assertTrue(row4.work.commenced)
        self.assertFalse(row4.work.stub)
        self.assertTrue(row4.work.principal)
        self.assertEqual(['Unknown commencement date', 'Principal work'], row4.notes)
        self.assertEqual([], row4.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], row4.tasks)

        row5 = works[4]
        self.assertEqual('success', row5.status)
        self.assertEqual('Principal work', row5.work.title)
        self.assertEqual('act', row5.work.nature)
        self.assertEqual('76', row5.work.number)
        self.assertEqual('2012', row5.work.year)
        self.assertEqual(datetime.date(2012, 10, 21), row5.work.publication_date)
        self.assertEqual(None, row5.work.commencement_date)
        self.assertTrue(row5.work.commenced)
        self.assertFalse(row5.work.stub)
        self.assertTrue(row5.work.principal)
        self.assertEqual(['Unknown commencement date', 'Principal work'], row5.notes)
        self.assertEqual([], row5.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], row5.tasks)

        # not actually created though
        with self.assertRaises(Work.DoesNotExist):
            Work.objects.get(frbr_uri='/akn/za/act/2020/1')
        with self.assertRaises(Work.DoesNotExist):
            Work.objects.get(frbr_uri='/akn/za/act/2020/2')
        with self.assertRaises(Work.DoesNotExist):
            Work.objects.get(frbr_uri='/akn/za/debatereport/2020/1')

    def test_basic_live(self):
        works = self.get_works(False, 'basic.csv')
        self.assertEqual(5, len(works))

        work1 = Work.objects.get(frbr_uri='/akn/za/act/2020/1')
        row1 = works[0]
        self.assertEqual(work1, row1.work)
        self.assertEqual('Testy 1', work1.title)
        self.assertEqual('1', work1.number)
        self.assertEqual('2020', work1.year)
        self.assertEqual(datetime.date(2020, 1, 1), work1.publication_date)
        self.assertFalse(work1.stub)
        self.assertTrue(work1.principal)
        # no 'notes' when not in preview
        self.assertEqual([], row1.notes)
        self.assertEqual([], row1.relationships)
        tasks = work1.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

        work2 = Work.objects.get(frbr_uri='/akn/za/act/2020/2')
        row2 = works[1]
        self.assertEqual(work2, row2.work)
        self.assertEqual('Testy 2', work2.title)
        self.assertEqual('2', work2.number)
        self.assertEqual('2020', work2.year)
        self.assertEqual(datetime.date(2020, 6, 1), work2.publication_date)
        self.assertTrue(work2.stub)
        self.assertFalse(work2.principal)
        # no 'notes' when not in preview
        self.assertEqual([], row2.notes)
        self.assertEqual([], row2.relationships)
        tasks = work2.tasks.all()
        self.assertEqual(1, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)

        work3 = Work.objects.get(frbr_uri='/akn/za/debatereport/2020/et-à-l-information-financière')
        row3 = works[2]
        self.assertEqual(work3, row3.work)
        self.assertEqual('Testy 3', work3.title)
        self.assertEqual('et-à-l-information-financière', work3.number)
        self.assertEqual('2020', work3.year)
        self.assertEqual(datetime.date(2020, 6, 1), work3.publication_date)
        self.assertFalse(work3.stub)
        self.assertTrue(work3.principal)
        # no 'notes' when not in preview
        self.assertEqual([], row3.notes)
        self.assertEqual([], row3.relationships)
        tasks = work3.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

    def test_block_cancel_preview(self):
        works = self.get_works(True, 'basic.csv', form_data={'block_import_tasks': True, 'block_conversion_tasks': True, 'cancel_gazette_tasks': True})

        row1 = works[0]
        self.assertEqual(['link gazette (CANCELLED)', 'convert document (BLOCKED)', 'import content (BLOCKED)'], row1.tasks)

    def test_block_cancel_live(self):
        self.get_works(False, 'basic.csv', form_data={'block_import_tasks': True, 'block_conversion_tasks': True, 'cancel_gazette_tasks': True})

        work1 = Work.objects.get(frbr_uri='/akn/za/act/2020/1')
        conversion_task1 = work1.tasks.get(title='Convert document')
        import_task1 = work1.tasks.get(title='Import content')
        gazette_task1 = work1.tasks.get(title='Link gazette')
        self.assertEqual('blocked', conversion_task1.state)
        self.assertEqual('blocked', import_task1.state)
        self.assertEqual('cancelled', gazette_task1.state)

    def test_block_and_cancel_preview(self):
        """ Both blocking and cancelling a task results in it being cancelled.
        """
        works = self.get_works(True, 'basic.csv', form_data={'block_import_tasks': True, 'cancel_import_tasks': True})

        row1 = works[0]
        self.assertEqual(['link gazette', 'convert document', 'import content (CANCELLED)'], row1.tasks)

    def test_block_and_cancel_live(self):
        """ Both blocking and cancelling a task results in it being cancelled.
        """
        self.get_works(False, 'basic.csv', form_data={'block_import_tasks': True, 'cancel_import_tasks': True})

        work1 = Work.objects.get(frbr_uri='/akn/za/act/2020/1')
        import_task1 = work1.tasks.get(title='Import content')
        self.assertEqual('cancelled', import_task1.state)

    def test_errors(self):
        jhb = Locality.objects.get(pk=1)
        self.creator.locality = jhb
        # preview
        works = self.get_works(True, 'errors.csv')
        self.assertEqual(8, len(works))

        row1 = works[0]
        self.assertIsNone(row1.status)
        self.assertEqual('''{"country": [{"message": "This field is required.", "code": "required"}], "locality": [{"message": "Select a valid choice. xyz is not one of the available choices.", "code": "invalid_choice"}], "number": [{"message": "This field is required.", "code": "required"}], "year": [{"message": "Must be a year (yyyy).", "code": "invalid"}], "publication_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}], "assent_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}]}''',
                         row1.errors.as_json())

        row2 = works[1]
        self.assertEqual('success', row2.status)
        self.assertEqual({}, row2.errors)

        row3 = works[2]
        self.assertIsNone(row3.status)
        self.assertEqual('''{"commencement_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}]}''',
                         row3.errors.as_json())

        row4 = works[3]
        self.assertIsNone(row4.status)
        self.assertEqual('''{"locality": [{"message": "Select a valid choice. cpt is not one of the available choices.", "code": "invalid_choice"}]}''',
                         row4.errors.as_json())

        row5 = works[4]
        self.assertIsNone(row5.status)
        self.assertEqual('''{"subtype": [{"message": "Select a valid choice. ln is not one of the available choices.", "code": "invalid_choice"}]}''',
                         row5.errors.as_json())

        row6 = works[5]
        self.assertIsNone(row6.status)
        self.assertEqual('''{"number": [{"message": "No spaces or punctuation allowed (use '-' for spaces).", "code": "invalid"}]}''',
                         row6.errors.as_json())

        row7 = works[5]
        self.assertIsNone(row7.status)
        self.assertEqual('''{"number": [{"message": "No spaces or punctuation allowed (use '-' for spaces).", "code": "invalid"}]}''',
                         row7.errors.as_json())

        row8 = works[5]
        self.assertIsNone(row8.status)
        self.assertEqual('''{"number": [{"message": "No spaces or punctuation allowed (use '-' for spaces).", "code": "invalid"}]}''',
                         row8.errors.as_json())

        # live
        works = self.get_works(False, 'errors.csv')
        row1 = works[0]
        with self.assertRaises(AttributeError):
            row1.work
        self.assertIsNone(row1.status)
        self.assertEqual('''{"country": [{"message": "This field is required.", "code": "required"}], "locality": [{"message": "Select a valid choice. xyz is not one of the available choices.", "code": "invalid_choice"}], "number": [{"message": "This field is required.", "code": "required"}], "year": [{"message": "Must be a year (yyyy).", "code": "invalid"}], "publication_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}], "assent_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}]}''',
                         row1.errors.as_json())

        row2 = works[1]
        work2 = Work.objects.get(frbr_uri='/akn/za-jhb/act/2020/2')
        self.assertEqual(work2, row2.work)
        self.assertEqual('success', row2.status)
        self.assertEqual({}, row2.errors)

        row3 = works[2]
        with self.assertRaises(AttributeError):
            row3.work
        self.assertIsNone(row3.status)
        self.assertEqual('''{"commencement_date": [{"message": "Date format should be yyyy-mm-dd.", "code": "invalid"}]}''',
                         row3.errors.as_json())

        row4 = works[3]
        with self.assertRaises(AttributeError):
            row4.work
        self.assertIsNone(row4.status)
        self.assertEqual(
            '''{"locality": [{"message": "Select a valid choice. cpt is not one of the available choices.", "code": "invalid_choice"}]}''',
            row4.errors.as_json())

        row5 = works[4]
        with self.assertRaises(AttributeError):
            row5.work
        self.assertIsNone(row5.status)
        self.assertEqual(
            '''{"subtype": [{"message": "Select a valid choice. ln is not one of the available choices.", "code": "invalid_choice"}]}''',
            row5.errors.as_json())

    def test_get_frbr_uri(self):
        row = SpreadsheetRow({}, {})
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
        self.assertEqual(['link gazette', 'convert document', 'import content', 'link primary work'], row3.tasks)

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
        # preview
        works = self.get_works(True, 'children.csv')
        row1 = works[0]
        # children found
        self.assertEqual([
            'Primary work of /akn/za/act/2020/2 (about to be imported)',
            'Primary work of /akn/za/act/2020/3 (about to be imported)'],
            row1.relationships)
        # child not found
        self.assertEqual(4, len(row1.tasks))
        self.assertIn('convert document', row1.tasks)
        self.assertIn('import content', row1.tasks)
        self.assertIn('link gazette', row1.tasks)
        self.assertIn('link subleg', row1.tasks)
        self.assertEqual(1, row1.tasks.count('link subleg'))

        # live
        works = self.get_works(False, 'children.csv')
        parent = works[0].work
        tasks = [t.title for t in parent.tasks.all()]
        child1 = works[1].work
        child2 = works[2].work
        child3 = works[3].work
        # children found
        self.assertEqual([
            'Primary work of /akn/za/act/2020/2 (about to be imported)',
            'Primary work of /akn/za/act/2020/3 (about to be imported)'],
            row1.relationships)
        # child not found
        self.assertEqual(1, tasks.count('Link subleg'))
        # success
        self.assertEqual(parent, child1.parent_work)
        self.assertEqual(parent, child2.parent_work)
        self.assertIsNone(child3.parent_work)

        # preview
        works = self.get_works(True, 'children_2.csv')
        row1 = works[0]
        # child 1 and 2 already have a parent
        self.assertIn('/akn/za/act/2020/2 (Child) already has a primary work', row1.notes)
        self.assertIn('/akn/za/act/2020/3 (Second child) already has a primary work', row1.notes)
        # child 3 will now be linked
        self.assertEqual(['Primary work of /akn/za/act/2020/4 (Third child)'], row1.relationships)

        # live
        works = self.get_works(False, 'children_2.csv')
        new_parent = works[0].work
        child3 = Work.objects.get(pk=child3.pk)
        # child 1 and 2 already have a parent
        self.assertEqual(parent, child1.parent_work)
        self.assertEqual(parent, child2.parent_work)
        self.assertIn('Check / update primary work', [t.title for t in child1.tasks.all()])
        self.assertIn('Check / update primary work', [t.title for t in child2.tasks.all()])
        # child 3 will now be linked
        self.assertEqual(new_parent, child3.parent_work)

    def test_link_commencements_passive(self):
        # preview (commencement objects aren't created)
        works = self.get_works(True, 'commencements_passive.csv')
        uncommenced = works[0]
        both = works[1]
        date_only = works[2]
        commenced_by_only = works[3]
        commencement_notice = works[4]
        error = works[5]
        commenced_by_and_commenced_on_date = works[6]
        commenced_on_date_only = works[7]

        # uncommenced
        self.assertEqual(['Uncommenced', 'Principal work'], uncommenced.notes)
        self.assertEqual([], uncommenced.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], uncommenced.tasks)

        # both
        self.assertEqual(['Principal work'], both.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/5 - '
                          'Commencement notice 1 (about to be imported) '
                          'on 2020-06-05'],
                         both.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], both.tasks)

        # date only
        self.assertEqual(['Principal work'], date_only.notes)
        self.assertEqual([], date_only.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], date_only.tasks)

        # commenced_by only
        self.assertEqual(['Unknown commencement date', 'Principal work'], commenced_by_only.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/5 - '
                          'Commencement notice 1 (about to be imported) '
                          'on (unknown)'],
                         commenced_by_only.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], commenced_by_only.tasks)

        # commencement notice
        self.assertEqual(['Stub'], commencement_notice.notes)
        self.assertEqual([], commencement_notice.relationships)
        self.assertEqual(['link gazette'], commencement_notice.tasks)

        # error
        self.assertEqual(['Principal work'], error.notes)
        self.assertEqual([], error.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content', 'link commencement passive'], error.tasks)

        # commenced_by_and_commenced_on_date
        self.assertEqual(['Principal work'], commenced_by_and_commenced_on_date.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/5 - '
                          'Commencement notice 1 (about to be imported) '
                          'on 2020-08-01'],
                         commenced_by_and_commenced_on_date.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], commenced_by_and_commenced_on_date.tasks)

        # commenced_on_date_only
        self.assertEqual(['Principal work'], commenced_on_date_only.notes)
        self.assertEqual([], commenced_on_date_only.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], commenced_on_date_only.tasks)

        # live
        works = self.get_works(False, 'commencements_passive.csv')
        uncommenced = works[0]
        both = works[1]
        date_only = works[2]
        commenced_by_only = works[3]
        commencement_notice = works[4]
        error = works[5]
        commenced_by_and_commenced_on_date = works[6]
        commenced_on_date_only = works[7]

        # uncommenced
        self.assertFalse(uncommenced.work.commenced)
        self.assertIsNone(uncommenced.work.commencement_date)
        self.assertIsNone(uncommenced.work.commencing_work)
        self.assertEqual([], uncommenced.notes)
        self.assertEqual([], uncommenced.relationships)
        tasks = uncommenced.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
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
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

        # date only
        self.assertTrue(date_only.work.commenced)
        self.assertEqual(datetime.date(2020, 6, 5),
                         date_only.work.commencement_date)
        self.assertIsNone(date_only.work.commencing_work)
        self.assertEqual([], date_only.notes)
        self.assertEqual([], date_only.relationships)
        tasks = date_only.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

        # commenced_by only
        self.assertTrue(commenced_by_only.work.commenced)
        self.assertIsNone(commenced_by_only.work.commencement_date)
        self.assertEqual(commencement_notice.work,
                         commenced_by_only.work.commencing_work)
        self.assertEqual([], both.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/5 (Commencement notice 1) on (unknown)'], commenced_by_only.relationships)
        tasks = commenced_by_only.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
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
        self.assertEqual(4, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)
        self.assertIn('Link commencement (passive)', task_titles)

        # commenced_by_and_commenced_on_date
        self.assertTrue(commenced_by_and_commenced_on_date.work.commenced)
        self.assertEqual(datetime.date(2020, 8, 1),
                         commenced_by_and_commenced_on_date.work.commencement_date)
        self.assertEqual(commencement_notice.work, commenced_by_and_commenced_on_date.work.commencing_work)
        self.assertEqual([], commenced_by_and_commenced_on_date.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/5 (Commencement notice 1) on 2020-08-01'],
                         commenced_by_and_commenced_on_date.relationships)
        tasks = commenced_by_and_commenced_on_date.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

        # commenced_on_date_only
        self.assertTrue(commenced_on_date_only.work.commenced)
        self.assertEqual(datetime.date(2020, 8, 1),
                         commenced_on_date_only.work.commencement_date)
        self.assertIsNone(commenced_on_date_only.work.commencing_work)
        self.assertEqual([], commenced_on_date_only.notes)
        self.assertEqual([], commenced_on_date_only.relationships)
        tasks = commenced_on_date_only.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

        # commenced later, preview
        works = self.get_works(True, 'commencements_passive_later.csv')
        now_commenced = works[0]
        self.assertEqual('duplicate', now_commenced.status)
        self.assertTrue(now_commenced.commenced)
        self.assertEqual(datetime.date(2020, 9, 1), now_commenced.commenced_on_date)
        self.assertIsNotNone(now_commenced.commenced_by)
        # but commencement object doesn't exist yet
        self.assertIsNone(now_commenced.work.commencement_date)
        self.assertEqual(['Principal work'], now_commenced.notes)
        self.assertEqual(['Commenced by /akn/za/act/2020/9 - '
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
        self.assertEqual(['Commenced by /akn/za/act/2020/9 (Commencement notice 2) on 2020-09-01'],
                         now_commenced.relationships)
        tasks = actual.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

    def test_link_commencements_active(self):
        # preview (commencement objects aren't created)
        works = self.get_works(True, 'commencements_active.csv')
        uncommenced = works[0]
        both = works[1]
        commenced_by_only = works[2]
        commencement_notice_1 = works[3]
        commencement_notice_2 = works[4]
        commencement_notice_3 = works[5]

        # uncommenced
        self.assertEqual(['Uncommenced', 'Principal work'], uncommenced.notes)
        self.assertEqual([], uncommenced.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], uncommenced.tasks)

        # both
        self.assertEqual(['Principal work'], both.notes)
        self.assertEqual([], both.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], both.tasks)

        # commenced_by only
        self.assertEqual(['Uncommenced', 'Principal work'], commenced_by_only.notes)
        self.assertEqual([], commenced_by_only.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], commenced_by_only.tasks)

        # commencement notice 1
        self.assertEqual(['Stub', 'Duplicate in batch'], commencement_notice_1.notes)
        self.assertEqual(['Commences /akn/za/act/2020/2 (about to be imported) on 2020-06-05'], commencement_notice_1.relationships)
        self.assertEqual(['link gazette'], commencement_notice_1.tasks)

        # commencement notice 2
        self.assertEqual(['Stub', 'Duplicate in batch'], commencement_notice_2.notes)
        self.assertEqual([], commencement_notice_2.relationships)
        self.assertEqual(['link gazette', 'commences on date missing'], commencement_notice_2.tasks)

        # commencement notice 3
        self.assertEqual(['Stub', 'Duplicate in batch'], commencement_notice_3.notes)
        self.assertEqual([], commencement_notice_3.relationships)
        self.assertEqual(['link gazette', 'link commencement active'], commencement_notice_3.tasks)

        # live
        works = self.get_works(False, 'commencements_active.csv')
        uncommenced = works[0]
        both = works[1]
        commenced_by_only = works[2]
        commencement_notice_1 = works[3]
        commencement_notice_2 = works[4]
        commencement_notice_3 = works[5]

        # uncommenced
        self.assertFalse(uncommenced.work.commenced)
        self.assertIsNone(uncommenced.work.commencement_date)
        self.assertIsNone(uncommenced.work.commencing_work)
        self.assertEqual([], uncommenced.notes)
        self.assertEqual([], uncommenced.relationships)
        tasks = uncommenced.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

        # both
        self.assertTrue(both.work.commenced)
        # main_commencement is a cached property
        actual = Work.objects.get(pk=both.work.pk)
        self.assertEqual(datetime.date(2020, 6, 5),
                         actual.commencement_date)
        self.assertEqual(commencement_notice_1.work, actual.commencing_work)
        self.assertEqual([], both.notes)
        self.assertEqual([], both.relationships)
        tasks = both.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

        # commenced_by only
        self.assertFalse(commenced_by_only.work.commenced)
        self.assertIsNone(commenced_by_only.work.commencement_date)
        self.assertIsNone(commenced_by_only.work.commencing_work)
        self.assertEqual([], commenced_by_only.notes)
        self.assertEqual([], commenced_by_only.relationships)
        tasks = commenced_by_only.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

        # commencement notice 1
        self.assertEqual('success', commencement_notice_1.status)
        self.assertTrue(commencement_notice_1.work.commenced)
        self.assertEqual(datetime.date(2020, 7, 1),
                         commencement_notice_1.work.commencement_date)
        self.assertIsNone(commencement_notice_1.work.commencing_work)
        self.assertEqual([], commencement_notice_1.notes)
        self.assertEqual(['Commences /akn/za/act/2020/2 (Both date and commenced_by) on 2020-06-05'],
                         commencement_notice_1.relationships)
        tasks = commencement_notice_1.work.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn("'Commences on' date missing", task_titles)
        self.assertIn('Link commencement (active)', task_titles)

        # commencement notice 2
        self.assertEqual('duplicate', commencement_notice_2.status)
        self.assertEqual([], commencement_notice_2.notes)
        self.assertEqual([], commencement_notice_2.relationships)
        self.assertEqual(commencement_notice_1.work, commencement_notice_2.work)

        # commencement notice 3
        self.assertEqual('duplicate', commencement_notice_3.status)
        self.assertEqual([], commencement_notice_3.notes)
        self.assertEqual([], commencement_notice_3.relationships)
        self.assertEqual(commencement_notice_1.work, commencement_notice_3.work)

        # commenced later, preview
        works = self.get_works(True, 'commencements_active_later.csv')
        new_commencement_notice = works[0]

        self.assertEqual('success', new_commencement_notice.status)
        self.assertEqual(['Stub'], new_commencement_notice.notes)
        self.assertEqual(['Commences /akn/za/act/2020/1 (Uncommenced) on 2020-10-01'],
                         new_commencement_notice.relationships)
        self.assertEqual(['link gazette'], new_commencement_notice.tasks)

        # commenced later, live
        works = self.get_works(False, 'commencements_active_later.csv')
        now_commenced = Work.objects.get(pk=uncommenced.work.pk)
        new_commencement_notice = works[0]

        self.assertTrue(now_commenced.commenced)
        self.assertEqual(datetime.date(2020, 10, 1),
                         now_commenced.commencement_date)
        self.assertEqual(new_commencement_notice.work, now_commenced.commencing_work)
        tasks = now_commenced.tasks.all()
        self.assertEqual(3, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)

        self.assertEqual('success', new_commencement_notice.status)
        self.assertEqual([], new_commencement_notice.notes)
        self.assertEqual(['Commences /akn/za/act/2020/1 (Uncommenced) on 2020-10-01'],
                         new_commencement_notice.relationships)
        tasks = new_commencement_notice.work.tasks.all()
        self.assertEqual(1, len(tasks))
        task_titles = [t.title for t in tasks]
        self.assertIn('Link gazette', task_titles)

    def test_link_amendments_active(self):
        # preview
        works = self.get_works(True, 'amendments_active.csv')
        main = works[0]
        amend1 = works[1]
        amend2 = works[2]
        error = works[3]
        other_main = works[4]

        self.assertEqual('success', main.status)
        self.assertEqual('success', amend1.status)
        self.assertEqual('success', amend2.status)
        self.assertEqual('success', error.status)
        self.assertEqual('success', other_main.status)

        self.assertEqual(['Principal work'], main.notes)
        self.assertEqual([], main.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], main.tasks)

        self.assertEqual(['Principal work'], other_main.notes)
        self.assertEqual([], other_main.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], other_main.tasks)

        self.assertEqual(
            ['Stub', "An 'Apply amendment' task will be created on /akn/za/act/2020/1 – Main (about to be imported)"],
            amend1.notes)
        self.assertEqual(['Amends /akn/za/act/2020/1 – Main (about to be imported) on 2020-06-01'], amend1.relationships)
        self.assertEqual(['link gazette'], amend1.tasks)

        self.assertEqual([
            'Stub',
            "An 'Apply amendment' task will be created on /akn/za/act/2020/1 – Main (about to be imported)",
            "An 'Apply amendment' task will be created on /akn/za/act/2020/1x – Other Main (about to be imported)"],
            amend2.notes)
        self.assertEqual([
            'Amends /akn/za/act/2020/1 – Main (about to be imported) on 2020-08-01',
            'Amends /akn/za/act/2020/1x – Other Main (about to be imported) on 2020-08-01',
        ], amend2.relationships)
        self.assertEqual(['link gazette'], amend2.tasks)

        self.assertEqual(['Stub'], error.notes)
        self.assertEqual([], error.relationships)
        self.assertEqual(['link gazette', 'link amendment active'], error.tasks)

        # live
        works = self.get_works(False, 'amendments_active.csv')
        main = works[0].work
        amend1 = works[1].work
        amend2 = works[2].work
        error = works[3].work
        other_main = works[4].work

        amendments = main.amendments.all()
        self.assertEqual(2, len(amendments))
        amenders = [a.amending_work for a in amendments]
        self.assertIn(amend1, amenders)
        self.assertIn(amend2, amenders)
        dates = [a.date for a in amendments]
        self.assertIn(datetime.date(2020, 6, 1), dates)
        self.assertIn(datetime.date(2020, 8, 1), dates)

        amendments = other_main.amendments.all()
        self.assertEqual(1, len(amendments))
        amenders = [a.amending_work for a in amendments]
        self.assertNotIn(amend1, amenders)
        self.assertIn(amend2, amenders)
        dates = [a.date for a in amendments]
        self.assertIn(datetime.date(2020, 8, 1), dates)

        main_tasks = [t.title for t in main.tasks.all()]
        self.assertEqual(2, main_tasks.count('Apply amendment'))

        other_main_tasks = [t.title for t in other_main.tasks.all()]
        self.assertEqual(1, other_main_tasks.count('Apply amendment'))

        error_tasks = [t.title for t in error.tasks.all()]
        self.assertIn('Link amendment (active)', error_tasks)

        # TODO: add test for amendment of duplicate main work

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
        self.assertEqual(['Principal work', 'Duplicate in batch', "An 'Apply amendment' task will be created on this work"], main.notes)
        self.assertEqual(['Principal work', 'Duplicate in batch', "An 'Apply amendment' task will be created on this work"], dupe1.notes)
        self.assertEqual(['Principal work', 'Duplicate in batch', "An 'Apply amendment' task will be created on this work"], dupe2.notes)
        self.assertEqual(['Principal work', 'Duplicate in batch'], dupe3.notes)
        self.assertEqual(['Stub'], amend_1.notes)
        self.assertEqual(['Stub'], amend_2.notes)
        self.assertEqual(['Stub'], amend_3.notes)
        self.assertEqual(['Amended by /akn/za/act/2020/2 – First (about to be imported)'], main.relationships)
        self.assertEqual(['Amended by /akn/za/act/2020/3 – Second (about to be imported)'], dupe1.relationships)
        self.assertEqual(['Amended by /akn/za/act/2020/4 – Third (about to be imported)'], dupe2.relationships)
        self.assertEqual([], dupe3.relationships)
        self.assertEqual([], amend_1.relationships)
        self.assertEqual([], amend_2.relationships)
        self.assertEqual([], amend_3.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], main.tasks)
        self.assertEqual(['link gazette', 'convert document', 'import content'], dupe1.tasks)
        self.assertEqual(['link gazette', 'convert document', 'import content'], dupe2.tasks)
        self.assertEqual(['link gazette', 'convert document', 'import content', 'link amendment passive'], dupe3.tasks)
        self.assertEqual(['link gazette'], amend_1.tasks)
        self.assertEqual(['link gazette'], amend_2.tasks)
        self.assertEqual(['link gazette'], amend_3.tasks)

        # live
        works = self.get_works(False, 'amendments_passive.csv')
        main = works[0]
        dupe1 = works[1]
        dupe2 = works[2]
        dupe3 = works[3]
        amend_1 = works[4]
        amend_2 = works[5]
        amend_3 = works[6]

        self.assertEqual(main.work, dupe1.work)
        self.assertEqual(dupe1.work, dupe2.work)
        self.assertEqual(dupe2.work, dupe3.work)

        self.assertEqual('success', main.status)
        self.assertEqual('duplicate', dupe1.status)
        self.assertEqual('duplicate', dupe2.status)
        self.assertEqual('duplicate', dupe3.status)
        self.assertEqual('success', amend_1.status)
        self.assertEqual('success', amend_2.status)
        self.assertEqual('success', amend_3.status)
        self.assertEqual([], main.notes)
        self.assertEqual([], dupe1.notes)
        self.assertEqual([], dupe2.notes)
        self.assertEqual([], dupe3.notes)
        self.assertEqual([], amend_1.notes)
        self.assertEqual([], amend_2.notes)
        self.assertEqual([], amend_3.notes)
        self.assertEqual(['Amended by /akn/za/act/2020/2 (Amendment) on 2020-06-01'], main.relationships)
        self.assertEqual(['Amended by /akn/za/act/2020/3 (Second amendment) on 2020-08-01'], dupe1.relationships)
        # TODO: this should show up as an error (pending commencement) in preview
        self.assertEqual([], dupe2.relationships)
        self.assertEqual([], dupe3.relationships)
        self.assertEqual([], amend_1.relationships)
        self.assertEqual([], amend_2.relationships)
        self.assertEqual([], amend_3.relationships)

        amendments = main.work.amendments.all()
        self.assertEqual(2, len(amendments))
        amenders = [a.amending_work for a in amendments]
        self.assertIn(amend_1.work, amenders)
        self.assertIn(amend_2.work, amenders)
        dates = [a.date for a in amendments]
        self.assertIn(datetime.date(2020, 6, 1), dates)
        self.assertIn(datetime.date(2020, 8, 1), dates)

        tasks = main.work.tasks.all()
        task_titles = [t.title for t in tasks]
        self.assertEqual(6, len(tasks))
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Convert document', task_titles)
        self.assertIn('Import content', task_titles)
        self.assertIn('Link amendment (passive)', task_titles)
        self.assertEqual(2, task_titles.count('Apply amendment'))

        tasks = amend_3.work.tasks.all()
        task_titles = [t.title for t in tasks]
        self.assertEqual(2, len(tasks))
        self.assertIn('Link gazette', task_titles)
        self.assertIn('Link amendment (pending commencement)', task_titles)

    def test_link_amendments_active_block(self):
        # preview
        works = self.get_works(True, 'amendments_active.csv', {'block_amendment_tasks': True})
        amend1 = works[1]
        self.assertEqual(
            ['Stub', "An 'Apply amendment' task will be created on /akn/za/act/2020/1 – Main (about to be imported) and BLOCKED"],
            amend1.notes)

        amend2 = works[2]
        self.assertEqual([
            'Stub',
            "An 'Apply amendment' task will be created on /akn/za/act/2020/1 – Main (about to be imported) and BLOCKED",
            "An 'Apply amendment' task will be created on /akn/za/act/2020/1x – Other Main (about to be imported) and BLOCKED"],
            amend2.notes)

        # live
        works = self.get_works(False, 'amendments_active.csv', {'block_amendment_tasks': True})
        main = works[0].work
        other_main = works[4].work

        apply_amendment_tasks_main = main.tasks.filter(title='Apply amendment')
        for t in apply_amendment_tasks_main:
            self.assertEqual('blocked', t.state)

        apply_amendment_task_other = other_main.tasks.get(title='Apply amendment')
        self.assertEqual('blocked', apply_amendment_task_other.state)

    def test_link_amendments_passive_block(self):
        # preview
        works = self.get_works(True, 'amendments_passive.csv', {'block_amendment_tasks': True})
        main = works[0]
        dupe1 = works[1]
        dupe2 = works[2]
        self.assertEqual(['Principal work', 'Duplicate in batch', "An 'Apply amendment' task will be created on this work and BLOCKED"], main.notes)
        self.assertEqual(['Principal work', 'Duplicate in batch', "An 'Apply amendment' task will be created on this work and BLOCKED"], dupe1.notes)
        self.assertEqual(['Principal work', 'Duplicate in batch', "An 'Apply amendment' task will be created on this work and BLOCKED"], dupe2.notes)

        # live
        works = self.get_works(False, 'amendments_passive.csv', {'block_amendment_tasks': True})
        main = works[0]

        apply_amendment_tasks_main = main.work.tasks.filter(title='Apply amendment')
        for t in apply_amendment_tasks_main:
            self.assertEqual('blocked', t.state)

    def test_link_amendments_active_cancel(self):
        # preview
        works = self.get_works(True, 'amendments_active.csv', {'block_amendment_tasks': True, 'cancel_amendment_tasks': True})
        amend1 = works[1]
        self.assertEqual(
            ['Stub', "An 'Apply amendment' task will be created on /akn/za/act/2020/1 – Main (about to be imported) and CANCELLED"],
            amend1.notes)

        amend2 = works[2]
        self.assertEqual([
            'Stub',
            "An 'Apply amendment' task will be created on /akn/za/act/2020/1 – Main (about to be imported) and CANCELLED",
            "An 'Apply amendment' task will be created on /akn/za/act/2020/1x – Other Main (about to be imported) and CANCELLED"],
            amend2.notes)

        # live
        works = self.get_works(False, 'amendments_active.csv', {'block_amendment_tasks': True, 'cancel_amendment_tasks': True})
        main = works[0].work
        other_main = works[4].work

        apply_amendment_tasks_main = main.tasks.filter(title='Apply amendment')
        for t in apply_amendment_tasks_main:
            self.assertEqual('cancelled', t.state)

        apply_amendment_task_other = other_main.tasks.get(title='Apply amendment')
        self.assertEqual('cancelled', apply_amendment_task_other.state)

    def test_link_amendments_passive_cancel(self):
        # preview
        works = self.get_works(True, 'amendments_passive.csv', {'block_amendment_tasks': True, 'cancel_amendment_tasks': True})
        main = works[0]
        dupe1 = works[1]
        dupe2 = works[2]
        self.assertEqual(['Principal work', 'Duplicate in batch', "An 'Apply amendment' task will be created on this work and CANCELLED"], main.notes)
        self.assertEqual(['Principal work', 'Duplicate in batch', "An 'Apply amendment' task will be created on this work and CANCELLED"], dupe1.notes)
        self.assertEqual(['Principal work', 'Duplicate in batch', "An 'Apply amendment' task will be created on this work and CANCELLED"], dupe2.notes)

        # live
        works = self.get_works(False, 'amendments_passive.csv', {'block_amendment_tasks': True, 'cancel_amendment_tasks': True})
        main = works[0]

        apply_amendment_tasks_main = main.work.tasks.filter(title='Apply amendment')
        for t in apply_amendment_tasks_main:
            self.assertEqual('cancelled', t.state)

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

        self.assertEqual(['Principal work'], main1.notes)
        self.assertEqual(['Repealed by /akn/za/act/2020/2 (about to be imported)'], main1.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], main1.tasks)

        self.assertEqual(['Principal work'], main2.notes)
        self.assertEqual(['Repealed by /akn/za/act/2020/4 (about to be imported)'], main2.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], main2.tasks)

        self.assertEqual(['Principal work'], main3.notes)
        self.assertEqual([], main3.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content', 'no repealed by match'], main3.tasks)

        # live
        works = self.get_works(False, 'repeals_passive.csv')
        main1 = works[0].work
        repeal1 = works[1].work
        main2 = works[2].work
        repeal2 = works[3].work
        main3 = works[4].work
        main4 = works[5].work
        repeal3 = works[6].work

        self.assertEqual(main1.repealed_by, repeal1)
        self.assertEqual(main1.repealed_date, datetime.date(2020, 6, 3))
        self.assertNotIn('Link repeal', [t.title for t in main1.tasks.all()])
        self.assertIsNone(main2.repealed_by)
        self.assertIn('Link repeal (pending commencement)', [t.title for t in repeal2.tasks.all()])
        self.assertIsNone(main3.repealed_by)
        self.assertIn('Link repealed by', [t.title for t in main3.tasks.all()])
        self.assertEqual(main4.repealed_by, repeal3)
        self.assertEqual(main4.repealed_date, datetime.date(2020, 6, 1))

    def test_link_repeals_active(self):
        # TODO: add test for check-update-repeal
        # preview
        works = self.get_works(True, 'repeals_active.csv')
        main1 = works[0]
        repeal1 = works[1]
        repealfail = works[2]
        main2 = works[3]
        repeal2 = works[4]
        repeal3 = works[5]

        self.assertEqual('success', main1.status)
        self.assertEqual('success', repeal1.status)
        self.assertEqual('success', repealfail.status)
        self.assertEqual('success', main2.status)
        self.assertEqual('success', repeal2.status)
        self.assertEqual('success', repeal3.status)

        self.assertEqual(['Principal work'], main1.notes)
        self.assertEqual([], main1.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], main1.tasks)

        self.assertEqual(['Stub'], repeal1.notes)
        self.assertEqual(['Repeals /akn/za/act/2020/1 (about to be imported)'], repeal1.relationships)
        self.assertEqual(['link gazette'], repeal1.tasks)

        self.assertEqual(['Stub'], repealfail.notes)
        # TODO: the fact that this is going to result in an error should ideally be shown in preview
        self.assertEqual(['Repeals /akn/za/act/2020/1 (about to be imported)'], repealfail.relationships)
        self.assertEqual(['link gazette'], repealfail.tasks)

        self.assertEqual(['Principal work'], main2.notes)
        self.assertEqual([], main2.relationships)
        self.assertEqual(['link gazette', 'convert document', 'import content'], main2.tasks)

        self.assertEqual(['Uncommenced', 'Stub'], repeal2.notes)
        self.assertEqual(['Repeals /akn/za/act/2020/3 (about to be imported)'], repeal2.relationships)
        self.assertEqual(['link gazette', 'link repeal pending commencement'], repeal2.tasks)

        self.assertEqual(['Stub'], repeal3.notes)
        self.assertEqual([], repeal3.relationships)
        self.assertEqual(['link gazette', 'no repeals match'], repeal3.tasks)

        # live
        works = self.get_works(False, 'repeals_active.csv')
        main1 = works[0].work
        repeal1 = works[1].work
        repealfail = works[2].work
        main2 = works[3].work
        repeal2 = works[4].work
        repeal3 = works[5].work
        main3 = works[6].work
        repeal4 = works[7].work

        self.assertEqual(main1.repealed_by, repeal1)
        self.assertEqual(main1.repealed_date, datetime.date(2020, 6, 3))
        self.assertNotIn('Link repeal', [t.title for t in main1.tasks.all()])
        self.assertIn('Check / update repeal', [t.title for t in main1.tasks.all()])
        self.assertNotIn(main1, repealfail.repealed_works.all())
        self.assertIsNone(main2.repealed_by)
        self.assertIn('Link repeal (pending commencement)', [t.title for t in repeal2.tasks.all()])
        self.assertIn('Link repeal', [t.title for t in repeal3.tasks.all()])
        self.assertEqual(main3.repealed_by, repeal4)
        self.assertEqual(main3.repealed_date, datetime.date(2020, 6, 1))

    def test_duplicates(self):
        # preview
        works = self.get_works(True, 'duplicates.csv')
        work1 = works[0]
        work2 = works[1]
        self.assertEqual('success', work1.status)
        self.assertEqual('success', work2.status)
        self.assertEqual(['Principal work', 'Duplicate in batch'], work1.notes)
        self.assertEqual(['Uncommenced', 'Stub', 'Duplicate in batch'], work2.notes)

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

    def test_link_taxonomies(self):
        children = TaxonomyTopic.objects.get(pk=5)
        communications = TaxonomyTopic.objects.get(pk=6)
        topic_with_comma = TaxonomyTopic.objects.get(pk=7)

        # preview
        works = self.get_works(True, 'taxonomies.csv')
        w1 = works[0]
        w2 = works[1]
        w3 = works[2]
        w4 = works[3]
        w5 = works[4]
        self.assertIn(children, w1.taxonomy_topics)
        self.assertIn(communications, w1.taxonomy_topics)
        self.assertIn(children, w2.taxonomy_topics)
        self.assertIn('TaxonomyTopic not found: Animal Husbandry; Finance', w2.notes)
        self.assertIn('TaxonomyTopic not found: lawsafrica-subject-areas-people-and-work', w3.notes)
        self.assertIn(children, w4.taxonomy_topics)
        self.assertIn(communications, w4.taxonomy_topics)
        self.assertIn(children, w5.taxonomy_topics)
        self.assertIn(communications, w5.taxonomy_topics)
        self.assertIn(topic_with_comma, w5.taxonomy_topics)

        # live
        works = self.get_works(False, 'taxonomies.csv')
        w1_taxonomies = works[0].work.taxonomy_topics.all()
        w2 = works[1].work
        w2_tasks = w2.tasks.all()
        w2_taxonomies = w2.taxonomy_topics.all()
        w3 = works[2].work
        w3_tasks = w3.tasks.all()
        w3_taxonomies = w3.taxonomy_topics.all()
        w4_taxonomies = works[3].work.taxonomy_topics.all()
        w5_taxonomies = works[4].work.taxonomy_topics.all()
        self.assertEqual(2, len(w1_taxonomies))
        self.assertIn(children, w1_taxonomies)
        self.assertIn(communications, w1_taxonomies)
        self.assertEqual(1, len(w2_taxonomies))
        self.assertIn(children, w2_taxonomies)
        self.assertEqual(4, len(w2_tasks))
        self.assertIn('Link taxonomy', [t.title for t in w2_tasks])
        self.assertEqual(0, len(w3_taxonomies))
        self.assertEqual(4, len(w3_tasks))
        self.assertIn('Link taxonomy', [t.title for t in w3_tasks])
        self.assertEqual(2, len(w4_taxonomies))
        self.assertIn(children, w4_taxonomies)
        self.assertIn(communications, w4_taxonomies)
        self.assertEqual(3, len(w5_taxonomies))
        self.assertIn(children, w5_taxonomies)
        self.assertIn(communications, w5_taxonomies)
        self.assertIn(topic_with_comma, w5_taxonomies)

        # live again; tasks shouldn't be created again
        works = self.get_works(False, 'taxonomies.csv')
        w2_tasks = works[1].work.tasks.all()
        w3_tasks = works[2].work.tasks.all()
        self.assertEqual(4, len(w2_tasks))
        self.assertEqual(4, len(w3_tasks))

    def test_subtypes(self):
        # dry run
        works = self.get_works(True, 'subtypes.csv')

        row1 = works[0]
        self.assertEqual('si', row1.work.subtype)

        row2 = works[1]
        self.assertEqual('gn', row2.work.subtype)

        # live
        works = self.get_works(False, 'subtypes.csv')

        work1 = Work.objects.get(frbr_uri='/akn/za/act/si/2020/1')
        self.assertEqual(work1, works[0].work)
        self.assertEqual('si', work1.subtype)

        work2 = Work.objects.get(frbr_uri='/akn/za/act/gn/2020/2')
        self.assertEqual(work2, works[1].work)
        self.assertEqual('gn', work2.subtype)

    # TODO:
    #  - test_link_publication_document
    #  - test_create_task (include workflow too)
    #  - test_add_extra_properties
    #  - test_aliases: transform_aliases and transform_error_aliases
    #  - test subclasses of BaseBulkCreator, RowValidationFormBase
