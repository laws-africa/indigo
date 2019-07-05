from __future__ import unicode_literals

from allauth.account.utils import user_display

from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.conf import settings

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
def publication_document_name(work):
    parts = []
    if work.publication_name:
        parts.append(work.publication_name)
        if work.publication_number:
            parts.append('no {}'.format(work.publication_number))
    else:
        parts.append('publication document')

    return ' '.join(parts)
