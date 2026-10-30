from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.test import SimpleTestCase

from indigo.tasks import TaskBroker
from indigo_api.models import PublicationDocument
from indigo_app.views.works import publication_document_response


class PublicationDocumentResponseTest(SimpleTestCase):
    @patch('indigo_app.views.works.plugins.for_work')
    def test_uses_publication_document_resolver(self, for_work):
        publication_document = SimpleNamespace(work=object())
        expected = HttpResponse(status=307)
        resolver = for_work.return_value
        resolver.get_response.return_value = expected

        response = publication_document_response(publication_document)

        self.assertIs(response, expected)
        for_work.assert_called_once_with(
            'publication-document-resolver',
            publication_document.work,
        )
        resolver.get_response.assert_called_once_with(publication_document)


class PublicationDocumentFileTest(SimpleTestCase):
    @patch('indigo_api.models.works.plugins.for_work')
    def test_uses_publication_document_resolver(self, for_work):
        publication_document = SimpleNamespace(
            work=object(),
            file=None,
            trusted_url=None,
        )
        expected = ContentFile(b'gazette')
        resolver = for_work.return_value
        resolver.get_file.return_value = expected

        file = PublicationDocument.get_file(publication_document)

        self.assertIs(file, expected)
        resolver.get_file.assert_called_once_with(publication_document)


class PublicationDocumentTaskFileTest(SimpleTestCase):
    @patch('indigo.tasks.TaskFile')
    def test_uses_resolved_publication_document_file(self, TaskFile):
        publication_file = ContentFile(b'gazette')
        publication_document = SimpleNamespace(
            trusted_url=None,
            get_file=Mock(return_value=publication_file),
            filename='gazette.pdf',
        )
        task = SimpleNamespace(
            work=SimpleNamespace(publication_document=publication_document),
            save=Mock(),
        )
        broker = TaskBroker.__new__(TaskBroker)
        broker.save_input_file_using_publication_document_info = Mock()

        broker.make_input_task_file(task, use_publication_document=True)

        publication_document.get_file.assert_called_once_with()
        self.assertEqual('gazette.pdf', TaskFile.return_value.file.name)
        broker.save_input_file_using_publication_document_info.assert_called_once_with(
            TaskFile.return_value,
            task,
            publication_document,
        )
