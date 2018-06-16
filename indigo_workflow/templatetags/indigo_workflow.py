from __future__ import unicode_literals

from django import template
from viewflow.models import Task

register = template.Library()


@register.filter
def manage_permission_name(flow_class):
    return flow_class._meta.manage_permission_name
