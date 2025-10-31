import json

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
def user_profile_photo_thumbnail(user, height=32, width=32):
    if not user:
        return ''

    return format_html('<img src="{}" height="{}" width="{}" class="user-profile-photo">'.format(user.userprofile.profile_photo_url, height, width))


@register.filter
def jsonify(value):
    return json.dumps(value)


@register.filter
def lookup(dictionary, key):
    """ Returns the value of an item from a given dictionary, using the given key, if it exists.
        Use when nested template tags would otherwise be needed, e.g. instead of
        {% for k in list_of_keys %}
            <li>{{ dictionary.k }}</li> (which will look up `k`, not its value) or
            <li>{{ dictionary.{{ k }} }}</li> (which is invalid), use
            <li>{{ dictionary|lookup:k }}</li>
    """
    return dictionary.get(key, '')


@register.filter
def model_name(instance):
    """ Returns the model name of a given model instance. """
    return instance._meta.model_name
