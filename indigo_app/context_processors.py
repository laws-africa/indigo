from django.conf import settings


def general(request):
    """
    Add some useful context to templates.
    """
    return {
        'DEBUG': settings.DEBUG,
        'INDIGO_LIME_DEBUG': settings.INDIGO_LIME_DEBUG,
        'SUPPORT_EMAIL': settings.SUPPORT_EMAIL,
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
    }
