from django.views.generic import TemplateView

import viewflow.flow.views as views
from viewflow.flow.viewset import FlowViewSet as BaseFlowViewSet
from viewflow.models import Task


class HumanInteractionView(views.UpdateProcessView):
    pass


class ReviewTaskView(views.UpdateProcessView):
    template_name = 'indigo_workflow/general/review.html'


class TaskListView(TemplateView):
    template_name = 'indigo_workflow/task_list.html'

    def __init__(self, *args, **kwargs):
        super(TaskListView, self).__init__(*args, **kwargs)

        import indigo_workflow.flows
        self.flows = indigo_workflow.flows.all_flows

    def get_context_data(self, **kwargs):
        kwargs = super(TaskListView, self).get_context_data(**kwargs)
        kwargs['assigned_tasks'] = Task.objects.inbox(self.flows, self.request.user).order_by('-created')
        kwargs['available_tasks'] = Task.objects.queue(self.flows, self.request.user).order_by('-created')

        return kwargs


class FlowViewSet(BaseFlowViewSet):
    process_list_view = None
    inbox_list_view = None
    queue_list_view = None
    archive_list_view = None
