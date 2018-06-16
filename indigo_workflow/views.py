import viewflow.flow.views as views


class TaskDetailTemplateMixin(object):
    """ Use the task_detail.html template for this task.
    """
    def get_template_names(self):
        if self.template_name is None:
            flow_task = self.activation.flow_task
            opts = self.activation.flow_task.flow_class._meta

            return (
                '{}/{}/{}_detail.html'.format(opts.app_label, opts.flow_label, flow_task.name),
                '{}/{}/task_detail.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/task_detail.html')
        else:
            return [self.template_name]


class HumanInteractionView(TaskDetailTemplateMixin, views.UpdateProcessView):
    pass


class ReviewTaskView(TaskDetailTemplateMixin, views.UpdateProcessView):
    pass
