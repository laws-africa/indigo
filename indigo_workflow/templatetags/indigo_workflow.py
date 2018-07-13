from __future__ import unicode_literals, absolute_import

from django import template
from viewflow.models import Task

from indigo_workflow.flows import single_work_flows
from indigo_workflow.urls import ns_map


register = template.Library()


@register.filter
def manage_permission_name(flow_class):
    return flow_class._meta.manage_permission_name


@register.filter
def human_tasks(tasks):
    return [t for t in tasks if t.flow_task_type == 'HUMAN']


@register.simple_tag
def assigned_work_tasks(work, user):

    tasks = Task.objects.inbox(single_work_flows, user)
    return [
        t for t in tasks
        if hasattr(t.flow_process, 'work') and t.flow_process.work == work
    ]


@register.simple_tag
def workflow_ns_map():
    return ns_map
