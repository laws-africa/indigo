from django.test import override_settings
from django.contrib.auth.models import User
from django_webtest import WebTest

from indigo_api.models import Task, Work, Workflow


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TasksTest(WebTest):
    fixtures = ['languages_data', 'countries', 'user', 'taxonomies', 'taxonomy_topics', 'work', 'editor', 'drafts', 'tasks']

    def setUp(self):
        self.app.set_user(User.objects.get(username='email@example.com'))

    def test_create_task(self):
        form = self.app.get('/places/za/tasks/new').forms['task-form']

        form['title'] = "test title"
        form['description'] = "test description"
        form['labels'] = ["1"]
        form['workflows'] = ['1']
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
        form['workflows'] = ['1']
        response = form.submit().follow()

        task = Task.objects.get(pk=response.context['task'].id)

        self.assertEqual(task.title, "test title")
        self.assertEqual(task.description, "test description")
        self.assertEqual([x.title for x in task.labels.all()], ["Label 1"])
        self.assertEqual(task.work, Work.objects.get(frbr_uri='/akn/za/act/2014/10'))

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

    def test_change_task_workflows(self):
        task = Task.objects.create(
            title="Test title",
            description="Test description",
            country_id=1,
            work=Work.objects.get(frbr_uri='/akn/za/act/2014/10'),
            created_by_user_id=1,
        )
        workflow = Workflow.objects.create(
            title='test workflow',
            country_id=1,
            created_by_user_id=1,
        )

        form = self.app.get(f'/places/za/tasks/{task.id}/').forms['task-workflow-form']
        form['workflows'] = str(workflow.id)
        form.submit().follow()

        task.refresh_from_db()
        self.assertEqual(list(task.workflows.all()), [workflow])

    def test_assign_task(self):
        task = Task.objects.create(
            title="Test title",
            description="Test description",
            country_id=1,
            work=Work.objects.get(frbr_uri='/akn/za/act/2014/10'),
            created_by_user_id=1,
        )
        csrf_token = self.app.get(f'/places/za/tasks/{task.pk}/').forms[0]['csrfmiddlewaretoken'].value

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
        csrf_token = self.app.get(f'/places/za/tasks/{task.pk}/').forms[0]['csrfmiddlewaretoken'].value

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

        response = self.app.get('/places/za/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('test title', response.text)

    def test_my_tasks(self):
        response = self.app.get('/tasks/')
        self.assertEqual(response.status_code, 200)

    def test_available_tasks(self):
        response = self.app.get('/tasks/available/')
        self.assertEqual(response.status_code, 200)

    def test_block_unblock_task(self):
        task = Task.objects.create(
            title="Test title",
            description="Test description",
            country_id=1,
            created_by_user_id=1,
        )
        blocking_task = Task.objects.create(
            title="Blocking task",
            description="Test description",
            country_id=1,
            created_by_user_id=1,
        )
        second_blocking_task = Task.objects.create(
            title="Second blocking task",
            description="Test description",
            country_id=1,
            created_by_user_id=1,
        )

        form = self.app.get(f'/places/za/tasks/{task.id}/').forms['task-blocked_by-form']
        form['blocked_by'] = [blocking_task.id]
        form.submit().follow()

        task.refresh_from_db()
        self.assertEqual(list(task.blocked_by.all()), [blocking_task])
        self.assertEqual(task.state, Task.BLOCKED)

        # update it
        form['blocked_by'] = [blocking_task.id, second_blocking_task.id]
        form.submit().follow()

        task.refresh_from_db()
        self.assertEqual(list(task.blocked_by.all()), [blocking_task, second_blocking_task])
        self.assertEqual(task.state, Task.BLOCKED)

        # now unblock it
        form['blocked_by'] = ''
        form.submit().follow()

        task.refresh_from_db()
        self.assertEqual(list(task.blocked_by.all()), [])
        self.assertEqual(task.state, Task.OPEN)
