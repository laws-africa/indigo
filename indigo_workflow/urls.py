from django.conf.urls import url, include

from .flows import ListWorksFlow, CreateWorksFlow
from .views import FlowViewSet
import indigo_workflow.views as views


urlpatterns = [
    url(r'^listworks/', include(FlowViewSet(ListWorksFlow).urls), name='list-works'),
    url(r'^createworks/', include(FlowViewSet(CreateWorksFlow).urls), name='list-works'),
    url(r'^tasks/', views.TaskListView.as_view(), name='tasks-dashboard'),
]
