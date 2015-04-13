from django.conf import settings

def general(request):
    """
    Add some useful context to templates.
    """
    return {
        'DEBUG': settings.DEBUG,
    }
