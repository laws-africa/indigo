from django.test import override_settings
from django.contrib.auth.models import User
from django_webtest import WebTest

from indigo_api.models import Task, Workflow


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WorkflowsTest(WebTest):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'work', 'editor', 'drafts', 'tasks']

    def setUp(self):
        self.user = User.objects.get(username='email@example.com')
        self.app.set_user(self.user)

    def test_create_workflow(self):
        form = self.app.get('/places/za/projects/new').forms['workflow-form']
        form['title'] = "test title"
        form['description'] = "test description"
        response = form.submit().follow()

        workflow = Workflow.objects.get(pk=response.context['workflow'].id)

        self.assertEqual(workflow.title, "test title")
        self.assertEqual(workflow.description, "test description")

        response = self.app.get('/places/za/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('test title', response.text)

    def test_edit_workflow(self):
        form = self.app.get('/places/za/projects/new').forms['workflow-form']
        form['title'] = "test title"
        form['description'] = "test description"
        response = form.submit().follow()

        workflow = Workflow.objects.get(pk=response.context['workflow'].id)

        form = self.app.get('/places/za/projects/%s/edit' % workflow.id).forms['workflow-form']
        form['title'] = "updated title"
        form['description'] = "updated description"
        response = form.submit().follow()

        workflow.refresh_from_db()
        self.assertEqual(workflow.title, "updated title")
        self.assertEqual(workflow.description, "updated description")

        response = self.app.get('/places/za/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('updated title', response.text)

    def test_add_tasks(self):
        form = self.app.get('/places/za/projects/new').forms['workflow-form']
        form['title'] = "test title"
        form['description'] = "test description"
        response = form.submit().follow()

        workflow = Workflow.objects.get(pk=response.context['workflow'].id)
        task = Task.objects.create(title="Task title", country=workflow.country, created_by_user=self.user)

        response = self.app.post('/places/za/projects/%s/tasks' % workflow.id, {
            'tasks': [task.id],
            'csrfmiddlewaretoken': response.context['csrf_token'],
        }).follow()
        self.assertEqual(response.status_code, 200)
        self.assertIn('Task title', response.text)

    def test_close_and_reopen_workflow(self):
        form = self.app.get('/places/za/projects/new').forms['workflow-form']
        form['title'] = "test title"
        form['description'] = "test description"
        response = form.submit().follow()

        workflow = Workflow.objects.get(pk=response.context['workflow'].id)

        response = self.app.post('/places/za/projects/%s/close' % workflow.id, {'csrfmiddlewaretoken': response.context['csrf_token']}).follow()
        self.assertEqual(response.status_code, 200)

        workflow.refresh_from_db()
        self.assertTrue(workflow.closed)

        response = self.app.post('/places/za/projects/%s/reopen' % workflow.id, {'csrfmiddlewaretoken': response.context['csrf_token']}).follow()
        self.assertEqual(response.status_code, 200)

        workflow.refresh_from_db()
        self.assertFalse(workflow.closed)
