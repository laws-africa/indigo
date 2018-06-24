from django.conf.urls import url, include
from viewflow.flow.viewset import FlowViewSet

from .flows import ListWorksFlow
import indigo_workflow.views as views


list_works_set = FlowViewSet(ListWorksFlow)
list_works_set.process_list_view = None
list_works_set.inbox_list_view = None
list_works_set.queue_list_view = None
list_works_set.archive_list_view = None

urlpatterns = [
    url(r'^listworks/', include(list_works_set.urls), name='list-works'),
    url(r'^tasks/', views.TaskListView.as_view(), name='all-task-list'),
]
