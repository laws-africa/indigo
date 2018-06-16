from viewflow import flow
from viewflow.base import this, Flow

from indigo_workflow import views
from indigo_workflow.models import ListWorksProcess


@flow.flow_start_func
def start_list_works_flow(activation, country, locality):
    activation.prepare()
    activation.process.country = country
    activation.process.locality = locality
    activation.done()
    return activation


class ListWorksFlow(Flow):
    process_class = ListWorksProcess
    summary_template = "List works for {{ process.place_name }}"

    start = (
        flow.StartFunction(start_list_works_flow)
        .Next(this.instructions)
    )

    # wait for human to do the work and then move the task into the next state
    instructions = (
        # show the regular task detail view for this task
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
            task_description="Review and approve listed works.",
            task_result_summary="Works were reviewed.",
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
