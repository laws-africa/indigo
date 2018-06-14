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

    start = (
        flow.StartFunction(start_list_works_flow)
        .Next(this.instructions)
    )

    # wait for human to do the work and then move the task into the next state
    instructions = (
        flow.View(views.ListWorksView)
        .Next(this.review)
    )

    review = (
        flow.View(views.ReviewTaskView)
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
