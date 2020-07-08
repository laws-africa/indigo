"""
WSGI config for indigo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
if os.environ.get('DJANGO_ENV') == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'indigo.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'indigo.settings.base')

#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "indigo.settings.base")

from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise
application = get_wsgi_application()
application = DjangoWhiteNoise(application)
