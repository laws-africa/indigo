from viewflow import flow
from viewflow.base import this, Flow

from indigo_workflow import views
from indigo_workflow.models import ListWorksProcess, CreateWorksProcess


class ListWorksFlow(Flow):
    """ Research works for a place and list them in the linked spreadsheet.
    """
    process_class = ListWorksProcess
    summary_template = "List works for {{ process.place_name }}"

    start = (
        flow.StartFunction(this.start_workflow)
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
        # TODO: appropriate permission
        .Permission('indigo_workflow.can_review_documents')
        .Next(this.check_approved)
    )

    check_approved = (
        flow.If(lambda a: a.process.approved)
        .Then(this.end)
        .Else(this.instructions)
    )

    end = flow.End()

    @staticmethod
    @flow.flow_start_func
    def start_workflow(activation, country, locality, notes):
        activation.prepare()
        activation.process.country = country
        activation.process.locality = locality
        activation.process.notes = notes
        activation.done()
        return activation


class CreateWorksFlow(Flow):
    """ Create works for the items listed in the linked spreadsheet.
    """
    process_class = CreateWorksProcess
    summary_template = "Create works for {{ process.place_name }}"

    start = (
        flow.StartFunction(this.start_workflow)
        .Next(this.instructions)
    )

    # wait for human to do the work and then move the task into the next state
    instructions = (
        flow.View(
            views.HumanInteractionView,
            task_title="Create works for items in a spreadsheet",
            task_description="Create a work for each item listed in the linked spreadsheet.",
            task_result_summary="{{ flow_task.task_description }}",
        )
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
        # TODO: appropriate permission
        .Permission('indigo_workflow.can_review_documents')
        .Next(this.check_approved)
    )

    check_approved = (
        flow.If(lambda a: a.process.approved)
        .Then(this.end)
        .Else(this.instructions)
    )

    end = flow.End()

    @staticmethod
    @flow.flow_start_func
    def start_workflow(activation, country, locality, notes):
        activation.prepare()
        activation.process.country = country
        activation.process.locality = locality
        activation.process.notes = notes
        activation.done()
        return activation
