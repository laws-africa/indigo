from django.conf.urls import url, include

from .flows import ListWorksFlow, CreateWorksFlow, ReviewWorkFlow, CreatePointInTimeFlow
from .views import FlowViewSet
import indigo_workflow.views as views

ns_map = {
    ListWorksFlow: 'listworks',
    CreateWorksFlow: 'createworks',
    ReviewWorkFlow: 'reviewwork',
    CreatePointInTimeFlow: 'create-pit',
}

urlpatterns = [url(r'^%s' % short, include(FlowViewSet(cls).urls, namespace=short)) for cls, short in ns_map.iteritems()]
urlpatterns += [
    url(r'^tasks/', views.TaskListView.as_view(ns_map=ns_map), name='tasks-dashboard'),
    url(r'^works(?P<frbr_uri>/\S+?)/workflows/$', views.WorkWorkflowsView.as_view(), name='work_workflows'),
]
