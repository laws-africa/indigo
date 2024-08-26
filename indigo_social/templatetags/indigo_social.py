from django import template

from indigo_social.models import BadgeAward

register = template.Library()


@register.simple_tag
def badges_for_user(user):
    """
    Sets the badges for a given user to a context var.  Usage:

        {% badges_for_user user as badges %}
    """
    return BadgeAward.objects.filter(user=user).order_by("-awarded_at")
