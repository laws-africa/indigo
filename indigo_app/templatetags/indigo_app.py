from __future__ import unicode_literals

from allauth.account.utils import user_display

from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.conf import settings

from indigo_api.models import Task

register = template.Library()


@register.simple_tag
def user_profile(user):
    """ Formatted link to a user's profile, using their display name.
    """
    if not user:
        return ''

    username = user_display(user)
    profile_url = settings.INDIGO_USER_PROFILE_URL
    if profile_url:
        url = reverse('indigo_social:user_profile', kwargs={'username': user.username})
        html = format_html('<a href="{}">{}</a>', url, username)
    else:
        html = username

    return html


@register.simple_tag
def task_list(place, work=None, frbr_uri=None, active=False):

    if work:
        frbr_uri = work.frbr_uri

    if hasattr(place.country, 'code'):
        country = place.country
    else:
        country = place.country.country

    locality = place if place.code != country.code else None

    tasks = Task.objects.filter(country=country, locality=locality).order_by('-created_at')

    if frbr_uri:
        tasks = tasks.filter(work__frbr_uri=frbr_uri)

    if active:
        tasks = tasks.exclude(state='cancelled').exclude(state='done')

    return tasks
