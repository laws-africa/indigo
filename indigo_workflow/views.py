import json
from django.views.generic import TemplateView, FormView

import viewflow.flow.views as views
from viewflow.flow.viewset import FlowViewSet as BaseFlowViewSet
from viewflow.flow.views.mixins import FlowListMixin
from viewflow.models import Task

from indigo_app.views import AbstractWorkView
from .forms import ImplicitPlaceProcessForm


class FlowViewSet(BaseFlowViewSet):
    process_list_view = None
    inbox_list_view = None
    queue_list_view = None
    archive_list_view = None


class HumanInteractionView(views.UpdateProcessView):
    pass


class ReviewTaskView(views.UpdateProcessView):
    template_name = 'indigo_workflow/general/review.html'


class TaskListView(TemplateView, FlowListMixin):
    template_name = 'indigo_workflow/task_list.html'

    def get_context_data(self, **kwargs):
        context_data = super(TaskListView, self).get_context_data(**kwargs)
        context_data['assigned_tasks'] = Task.objects.inbox(self.flows, self.request.user).order_by('-created')
        context_data['available_tasks'] = Task.objects.queue(self.flows, self.request.user).order_by('-created')
        context_data['available_flows'] = [
            f for f in self.flows
            if hasattr(f.start, 'can_execute') and f.start.can_execute(self.request.user)]
        return context_data


class StartPlaceWorkflowView(views.StartFlowMixin, FormView):
    template_name = 'indigo_workflow/general/start_place.html'
    form_class = ImplicitPlaceProcessForm

    def get_form_kwargs(self):
        kwargs = super(StartPlaceWorkflowView, self).get_form_kwargs()
        # bind the form to this process instance
        kwargs['instance'] = self.activation.process
        return kwargs

    def get_initial(self):
        return {
            'country': self.request.user.editor.country,
        }

    def form_valid(self, form):
        form.save()
        return super(StartPlaceWorkflowView, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(StartPlaceWorkflowView, self).get_context_data(*args, **kwargs)

        countries = context['form'].fields['country'].queryset.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in countries})
        context['js_view'] = 'StartPlaceWorkflowView'

        return context


class WorkWorkflowsView(AbstractWorkView):
    template_name_suffix = '_workflows'
