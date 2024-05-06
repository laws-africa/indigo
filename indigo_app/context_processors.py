from django.conf import settings

import json

from django.utils.translation import get_language
from django.templatetags.static import static


def general(request):
    """
    Add some useful context to templates.
    """
    return {
        'DEBUG': settings.DEBUG,
        'SUPPORT_EMAIL': settings.SUPPORT_EMAIL,
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'RESOLVER_URL': settings.RESOLVER_URL,
        'INDIGO_ORGANISATION': settings.INDIGO_ORGANISATION,
        'USER_JSON': serialise_user(request),
        'MAINTENANCE_MODE': settings.INDIGO['MAINTENANCE_MODE'],
        'SENTRY_DSN': settings.SENTRY_DSN,
        'JS_I18N': json.dumps(js_i18n(request)),
    }


def models(request):
    """ Add some useful models to templates
    """
    from indigo_api.models import Country, Language

    countries = Country.objects.select_related('country').prefetch_related('localities', 'publication_set', 'country')

    return {
        'indigo_languages': Language.objects.select_related('language').prefetch_related('language'),
        'indigo_countries': countries,
        'indigo_countries_json': json.dumps({c.code: c.as_json() for c in countries}),
    }


def serialise_user(request):
    data = {}

    if request.user.is_authenticated:
        from indigo_app.serializers import UserDetailsSerializer
        data = UserDetailsSerializer(context={'request': request}).to_representation(request.user)

    return json.dumps(data)


def js_i18n(request):
    """ Configuration for i18next for javascript translations."""
    paths = {
        f'{ns}-{code}': static(f'i18n/{ns}-{code}.json')
        for code, name in settings.LANGUAGES
        for ns in settings.INDIGO['JS_I18N_NAMESPACES']
    }

    return {
        'loadPaths': paths,
        'ns': 'indigo_app',
        'lng': get_language(),
        'fallbackLng': 'en',
        'returnEmptyString': False,
        'keySeparator': False,
        'debug': settings.DEBUG,
    }
