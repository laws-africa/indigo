from django.conf.urls import url, include

from .flows import ListWorksFlow, CreateWorksFlow
from .views import FlowViewSet
import indigo_workflow.views as views

ns_map = {
    ListWorksFlow: 'listworks',
    CreateWorksFlow: 'createworks',
}

urlpatterns = [
    url(r'^listworks/', include(FlowViewSet(ListWorksFlow).urls, namespace=ns_map[ListWorksFlow])),
    url(r'^createworks/', include(FlowViewSet(CreateWorksFlow).urls, namespace=ns_map[CreateWorksFlow])),
    url(r'^tasks/', views.TaskListView.as_view(ns_map=ns_map), name='tasks-dashboard'),
]
