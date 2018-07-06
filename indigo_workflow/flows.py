from viewflow import flow
from viewflow.base import this, Flow

from indigo_workflow import views
from indigo_workflow.models import ImplicitPlaceProcess
from django.utils.html import format_html


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


all_flows = [ListWorksFlow, CreateWorksFlow]
