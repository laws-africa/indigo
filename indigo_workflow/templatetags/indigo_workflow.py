from __future__ import unicode_literals

from django import template

register = template.Library()


@register.filter
def manage_permission_name(flow_class):
    return flow_class._meta.manage_permission_name


@register.filter
def human_tasks(tasks):
    return [t for t in tasks if t.flow_task_type == 'HUMAN']
