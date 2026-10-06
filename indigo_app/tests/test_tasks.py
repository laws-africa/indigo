import datetime
import shutil
from unittest import skipUnless

from django.test import override_settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django_webtest import WebTest

from indigo_api.models import Document, Task, TaskFile, Work
from indigo_app.tests.utils import TEST_STORAGES


@override_settings(STORAGES=TEST_STORAGES)
class TasksTest(WebTest):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomy_topics', 'work', 'editor', 'drafts', 'tasks']

    def setUp(self):
        self.app.set_user(User.objects.get(username='email@example.com'))

    @skipUnless(shutil.which('soffice'), 'LibreOffice is required for RTF conversion')
    def test_conversion_task_imports_rtf_through_shared_importer(self):
        work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        user = User.objects.get(username='email@example.com')
        source = (b'{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Arial;}}'
                  b'\\f0\\fs24 TEST ACT\\par 1. Short title\\par'
                  b'This Act may be cited as the Test Act.\\par}')
        output = TaskFile.objects.create(
            filename='example.rtf', mime_type='text/rtf', size=len(source),
        )
        task = Task.objects.create(
            title='Convert document', country=work.country, work=work,
            code='convert-document', timeline_date=datetime.date(2001, 1, 1),
            output_file=output, created_by_user=user,
        )
        output.file = ContentFile(source, name='example.rtf')
        output.save()

        task.finish(user)

        doc = Document.objects.get(work=work, expression_date=datetime.date(2001, 1, 1))
        self.assertIn('Short title', doc.content)
        self.assertEqual({a.filename for a in doc.attachments.all()}, {'example.rtf', 'example.docx'})

    def test_conversion_task_without_output_file_finishes_without_document(self):
        work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        user = User.objects.get(username='email@example.com')
        expression_date = datetime.date(2001, 1, 1)
        task = Task.objects.create(
            title='Convert document', country=work.country, work=work,
            code='convert-document', timeline_date=expression_date,
            created_by_user=user)
        import_task = Task.objects.create(
            title='Import content', country=work.country, work=work,
            code='import-content', timeline_date=expression_date,
            created_by_user=user)
        import_task.blocked_by.add(task)
        import_task.block(user)

        task.finish(user)

        task.refresh_from_db()
        import_task.refresh_from_db()
        self.assertEqual(task.state, Task.DONE)
        self.assertEqual(import_task.state, Task.OPEN)
        self.assertIsNone(import_task.document_id)
        self.assertFalse(Document.objects.filter(work=work, expression_date=expression_date).exists())

    @skipUnless(shutil.which('soffice'), 'LibreOffice is required for RTF conversion')
    def test_conversion_task_can_import_another_document_at_same_date(self):
        work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        user = User.objects.get(username='email@example.com')
        expression_date = datetime.date(2001, 1, 1)
        existing = Document.objects.create(
            work=work, title=work.title, expression_date=expression_date,
            language=work.country.primary_language, created_by_user=user)
        source = (b'{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Arial;}}'
                  b'\\f0\\fs24 TEST ACT\\par 1. Short title\\par'
                  b'This Act may be cited as the Test Act.\\par}')
        output = TaskFile.objects.create(
            filename='example.rtf', mime_type='text/rtf', size=len(source))
        task = Task.objects.create(
            title='Convert document', country=work.country, work=work,
            code='convert-document', timeline_date=expression_date,
            output_file=output, created_by_user=user)
        output.file = ContentFile(source, name='example.rtf')
        output.save()

        task.finish(user)

        documents = Document.objects.filter(work=work, expression_date=expression_date)
        self.assertEqual(documents.count(), 2)
        self.assertTrue(documents.filter(pk=existing.pk).exists())
        self.assertIn('Short title', documents.exclude(pk=existing.pk).get().content)

    @skipUnless(shutil.which('soffice'), 'LibreOffice is required for RTF conversion')
    def test_conversion_task_prefers_its_blocked_import_task(self):
        work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        user = User.objects.get(username='email@example.com')
        expression_date = datetime.date(2001, 1, 1)
        source = (b'{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Arial;}}'
                  b'\\f0\\fs24 TEST ACT\\par 1. Short title\\par'
                  b'This Act may be cited as the Test Act.\\par}')
        output = TaskFile.objects.create(
            filename='example.rtf', mime_type='text/rtf', size=len(source))
        conversion = Task.objects.create(
            title='Convert document', country=work.country, work=work,
            code='convert-document', timeline_date=expression_date,
            output_file=output, created_by_user=user)
        output.file = ContentFile(source, name='example.rtf')
        output.save()
        other_import = Task.objects.create(
            title='Other import', country=work.country, work=work,
            code='import-content', timeline_date=expression_date, created_by_user=user)
        preferred_import = Task.objects.create(
            title='Preferred import', country=work.country, work=work,
            code='import-content', timeline_date=expression_date, created_by_user=user)
        preferred_import.blocked_by.add(conversion)
        preferred_import.block(user)

        conversion.finish(user)

        other_import.refresh_from_db()
        preferred_import.refresh_from_db()
        self.assertIsNone(other_import.document_id)
        self.assertIsNotNone(preferred_import.document_id)
        self.assertEqual(preferred_import.state, Task.OPEN)

    def test_failed_rtf_conversion_keeps_task_open_and_shows_error(self):
        work = Work.objects.get(frbr_uri='/akn/za/act/2014/10')
        user = User.objects.get(username='email@example.com')
        source = b'not an RTF file'
        output = TaskFile.objects.create(
            filename='example.rtf', mime_type='application/rtf', size=len(source),
        )
        task = Task.objects.create(
            title='Convert document', country=work.country, work=work,
            code='convert-document', timeline_date=datetime.date(2001, 1, 1),
            output_file=output, created_by_user=user,
        )
        output.file = ContentFile(source, name='example.rtf')
        output.save()

        self.client.force_login(user)
        response = self.client.post(f'/places/za/tasks/{task.pk}/finish', follow=True)

        self.assertContains(response, 'valid RTF file')
        task.refresh_from_db()
        self.assertEqual(task.state, 'open')
        self.assertFalse(Document.objects.filter(work=work, expression_date=datetime.date(2001, 1, 1)).exists())

    def test_create_task(self):
        form = self.app.get('/places/za/tasks/new').forms['task-form']

        form['title'] = "test title"
        form['description'] = "test description"
        form['labels'] = ["1"]
        response = form.submit().follow()

        task = Task.objects.get(pk=response.context['task'].id)

        self.assertEqual(task.title, "test title")
        self.assertEqual(task.description, "test description")
        self.assertEqual([x.title for x in task.labels.all()], ["Label 1"])

    def test_create_task_with_work(self):
        form = self.app.get('/places/za/tasks/new?frbr_uri=/akn/za/act/2014/10').forms['task-form']

        form['title'] = "test title"
        form['description'] = "test description"
        form['labels'] = ["1"]
        response = form.submit().follow()

        task = Task.objects.get(pk=response.context['task'].id)

        self.assertEqual(task.title, "test title")
        self.assertEqual(task.description, "test description")
        self.assertEqual([x.title for x in task.labels.all()], ["Label 1"])
        self.assertEqual(task.work, Work.objects.get(frbr_uri='/akn/za/act/2014/10'))

    def test_download_task_file_quotes_filename(self):
        task_file = TaskFile.objects.create(
            filename='Gazette, 12.pdf',
            mime_type='application/pdf',
            size=4,
        )
        task = Task.objects.create(
            title='Test title',
            country_id=1,
            created_by_user_id=1,
            input_file=task_file,
        )
        task_file.file = ContentFile(b'test', name='Gazette, 12.pdf')
        task_file.save()

        response = self.app.get(f'/places/za/tasks/{task.pk}/input-file')

        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="Gazette, 12.pdf"',
        )

    def test_edit_task_with_work(self):
        task = Task.objects.create(
            title="Test title",
            description="Test description",
            country_id=1,
            work=Work.objects.get(frbr_uri='/akn/za/act/2014/10'),
            created_by_user_id=1,
        )

        form = self.app.get(f'/places/za/tasks/{task.id}/edit').forms[0]
        form['title'] = "Updated title"
        form.submit().follow()

        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated title')

    def test_assign_task(self):
        task = Task.objects.create(
            title="Test title",
            description="Test description",
            country_id=1,
            work=Work.objects.get(frbr_uri='/akn/za/act/2014/10'),
            created_by_user_id=1,
        )
        csrf_token = self.app.get(f'/places/za/tasks/{task.pk}').forms[0]['csrfmiddlewaretoken'].value

        # assign
        response = self.app.post(f'/places/za/tasks/{task.pk}/assign', params={
            'assigned_to': 1,
            'csrfmiddlewaretoken': csrf_token
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.assigned_to.id, 1)

        # unassign
        response = self.app.post(f'/places/za/tasks/{task.pk}/unassign', params={
            'csrfmiddlewaretoken': csrf_token
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertIsNone(task.assigned_to)

        # change assignment
        response = self.app.post(f'/places/za/tasks/{task.pk}/assign', params={
            'assigned_to': 2,
            'csrfmiddlewaretoken': csrf_token
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.assigned_to.id, 2)

    def test_submit_task(self):
        task = Task.objects.create(
            title="Test title",
            description="Test description",
            country_id=1,
            work=Work.objects.get(frbr_uri='/akn/za/act/2014/10'),
            created_by_user_id=1,
            assigned_to_id=1,
        )
        csrf_token = self.app.get(f'/places/za/tasks/{task.pk}').forms[0]['csrfmiddlewaretoken'].value

        # submit
        response = self.app.post(f'/places/za/tasks/{task.pk}/submit', params={
            'csrfmiddlewaretoken': csrf_token
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.state, 'pending_review')

        # unsubmit
        response = self.app.post(f'/places/za/tasks/{task.pk}/unsubmit', params={
            'csrfmiddlewaretoken': csrf_token
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.state, 'open')

    def test_place_tasks(self):
        form = self.app.get('/places/za/tasks/new').forms['task-form']
        form['title'] = "test title"
        form['description'] = "test description"
        response = form.submit()
        self.assertEqual(response.status_code, 302)

        response = self.app.get('/places/za/tasks')
        self.assertEqual(response.status_code, 200)
        self.assertIn('test title', response.text)

    def test_my_tasks(self):
        response = self.app.get('/tasks/')
        self.assertEqual(response.status_code, 200)

    def test_all_tasks(self):
        response = self.app.get('/tasks/all/')
        self.assertEqual(response.status_code, 200)
