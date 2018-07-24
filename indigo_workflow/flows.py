from django.utils.html import format_html
from django.dispatch import receiver
from viewflow import flow
from viewflow.base import this, Flow
from viewflow.activation import STATUS

from indigo_api.signals import work_changed
from indigo_workflow import views
from indigo_workflow.models import ImplicitPlaceProcess, ReviewWorkProcess, CreatePointInTimeProcess


class ListWorksFlow(Flow):
    """ Research works for a place and list them in the linked spreadsheet
    """
    process_class = ImplicitPlaceProcess
    summary_template = "List works for {{ process.place_name }}"

    start = (
        flow.Start(views.StartPlaceWorkflowView)
        .Permission('indigo_api.review_work')
        .Next(this.instructions)
    )

    # wait for human to do the work and then move the task into the next state
    instructions = (
        flow.View(
            views.HumanInteractionView,
            task_title="List work details in a spreadsheet",
            task_description="List the short title, publication date, gazette name and number in the linked spreadsheet.",
            task_result_summary="{{ flow_task.task_description }}",
        )
        .Permission('indigo_api.add_work')
        .Next(this.review)
    )

    review = (
        flow.View(
            views.ReviewTaskView,
            fields=['approved'],
            task_title="Review and approve listed works",
            task_description="Review the listed works in the spreadsheet. The task is done if the list is complete and has all required details for all works.",
            task_result_summary="{{ flow_task.task_description }}",
        )
        .Permission('indigo_api.review_work')
        .Next(this.check_approved)
    )

    check_approved = (
        flow.If(lambda a: a.process.approved)
        .Then(this.end)
        .Else(this.instructions)
    )

    end = flow.End()


class CreateWorksFlow(Flow):
    """ Create works for the items listed in the linked spreadsheet
    """
    process_class = ImplicitPlaceProcess
    summary_template = "Create works for {{ process.place_name }}"

    start = (
        flow.Start(views.StartPlaceWorkflowView)
        .Permission('indigo_api.review_work')
        .Next(this.instructions)
    )

    # wait for human to do the work and then move the task into the next state
    instructions = (
        flow.View(
            views.HumanInteractionView,
            task_title="Create works for items in a spreadsheet",
            task_description=format_html('<a href="/works/new">Create a work</a> for each item listed in the linked spreadsheet.'),
            task_result_summary="{{ flow_task.task_description }}",
        )
        .Permission('indigo_api.add_work')
        .Next(this.review)
    )

    review = (
        flow.View(
            views.ReviewTaskView,
            fields=['approved'],
            task_title="Review and approve listed works",
            task_description="Review the created works in the spreadsheet. The task is done if all the works have been created.",
            task_result_summary="{{ flow_task.task_description }}",
        )
        .Permission('indigo_api.review_work')
        .Next(this.check_approved)
    )

    check_approved = (
        flow.If(lambda a: a.process.approved)
        .Then(this.end)
        .Else(this.instructions)
    )

    end = flow.End()


class ReviewWorkFlow(Flow):
    """ Review the details of a work.
    """
    process_class = ReviewWorkProcess
    summary_template = "Review metadata for {{ process.work.frbr_uri }}"

    start = (
        flow.StartFunction(this.start_workflow)
        .Next(this.instructions)
    )

    # wait for human to do the work and then move the task into the next state
    instructions = (
        flow.View(
            views.HumanInteractionView,
            task_title="Review the metadata and details of the work",
            task_description=format_html('View the work. The task is done if the details are correct and accurate. Make corrections if necessary.'),
            task_result_summary="{{ flow_task.task_description }}",
        )
        .Permission('indigo_api.add_work')
        .Next(this.end)
    )

    end = flow.End()

    @staticmethod
    @flow.flow_start_func
    def start_workflow(activation, work):
        activation.prepare()
        activation.process.work = work
        activation.done()
        return activation

    @classmethod
    def get_or_create(cls, work):
        """ Get (or create a new) existing, unfinished process for a work.
        """
        process = cls.process_class.objects.filter(work=work, status=STATUS.NEW).first()
        if not process:
            activation = cls.start.run(work)
            process = activation.process
        return process


@receiver(work_changed)
def on_work_changed(sender, work, request, **kwargs):
    """ Create a new work review task for this work.
    """
    user = request.user
    if user and user.is_authenticated and not user.has_perm('indigo_api.review_work'):
        ReviewWorkFlow.get_or_create(work)


class CreatePointInTimeFlow(Flow):
    """ Create a new Point in Time for a work.
    """
    process_class = CreatePointInTimeProcess
    summary_template = "Create a new Point in Time for {{ process.work.frbr_uri }} at {{ process.date|date:'Y-m-d' }} in {{ language.name }}"

    start = (
        flow.Start(views.StartCreatePointInTimeView)
        .Permission('indigo_api.add_amendment')
        .Next(this.instructions)
    )

    # wait for human to do the work and then move the task into the next state
    instructions = (
        flow.View(
            views.HumanInteractionView,
            task_title="Consolidate or import a point in time version of the work",
            task_description=format_html('Visit the work\'s point in time page. Consolidate or import a version at the specific date, in the specific language.'),
            task_result_summary="{{ flow_task.task_description }}",
        )
        .Permission('indigo_api.add_document')
        .Next(this.review)
    )

    review = (
        flow.View(
            views.ReviewTaskView,
            fields=['approved'],
            task_title="Review and approve the created point in time",
            task_description="Review the document for the specific point in time and language. The task is done if the work has been correctly consolidated.",
            task_result_summary="{{ flow_task.task_description }}",
        )
        .Permission('indigo_api.review_document')
        .Next(this.check_approved)
    )

    check_approved = (
        flow.If(lambda a: a.process.approved)
        .Then(this.end)
        .Else(this.instructions)
    )

    end = flow.End()


# Workflows associated to a single work
single_work_flows = [ReviewWorkFlow, CreatePointInTimeFlow]
