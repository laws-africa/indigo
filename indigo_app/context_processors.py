from django.conf import settings

import json


def general(request):
    """
    Add some useful context to templates.
    """
    return {
        'DEBUG': settings.DEBUG,
        'SUPPORT_EMAIL': settings.SUPPORT_EMAIL,
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'RESOLVER_URL': settings.RESOLVER_URL,
        'USER_JSON': serialise_user(request),
    }


def models(request):
    """ Add some useful models to templates
    """
    from indigo_api.models import Country, Language

    return {
        'indigo_languages': Language.objects.select_related('language').prefetch_related('language'),
        'indigo_countries': Country.objects.select_related('country').prefetch_related('localities', 'publication_set', 'country'),
    }


def serialise_user(request):
    data = {}

    if request.user.is_authenticated():
        from indigo_app.serializers import UserDetailsSerializer
        data = UserDetailsSerializer(context={'request': request}).to_representation(request.user)

    return json.dumps(data)
