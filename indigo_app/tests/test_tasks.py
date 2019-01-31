from django.test import override_settings
from django.contrib.auth.models import User
from django_webtest import WebTest

from indigo_api.models import Task


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TasksTest(WebTest):
    fixtures = ['countries', 'user', 'work', 'editor', 'drafts', 'tasks']

    def setUp(self):
        self.app.set_user(User.objects.get(username='email@example.com'))

    def test_create_task(self):
        form = self.app.get('/places/za/tasks/new').forms['task-form']

        form['title'] = "test title"
        form['description'] = "test description"
        form['labels'] = ["1"]
        response = form.submit().follow()

        task = Task.objects.get(pk=response.context['task'].id)

        self.assertEqual(task.title, "test title")
        self.assertEqual(task.description, "test description")
        self.assertEqual([x.title for x in task.labels.all()], [u"Label 1"])
