from django.conf import settings

def general(request):
    """
    Add some useful context to templates.
    """
    return {
        'DEBUG': settings.DEBUG,
        'INDIGO_LIME_DEBUG': settings.INDIGO_LIME_DEBUG,
    }
