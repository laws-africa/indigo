from django.views.generic import TemplateView

import viewflow.flow.views as views
from viewflow.models import Task


class HumanInteractionView(views.UpdateProcessView):
    pass


class ReviewTaskView(views.UpdateProcessView):
    pass


class TaskListView(TemplateView):
    template_name = 'indigo_workflow/task_list.html'

    def __init__(self, *args, **kwargs):
        super(TaskListView, self).__init__(*args, **kwargs)

        from indigo_workflow.flows import ListWorksFlow
        self.flows = [ListWorksFlow]

    def get_context_data(self, **kwargs):
        kwargs = super(TaskListView, self).get_context_data(**kwargs)
        kwargs['assigned_tasks'] = Task.objects.inbox(self.flows, self.request.user).order_by('-created')
        kwargs['available_tasks'] = Task.objects.queue(self.flows, self.request.user).order_by('-created')

        return kwargs
