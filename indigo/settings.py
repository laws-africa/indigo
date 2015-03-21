"""
Django settings for indigo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

import sys
sys.path.append(BASE_DIR + '/lib')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'true') == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
if DEBUG:
    SECRET_KEY = 'j5ikpmmn&1hce#&_8!p)mx5y&*)m$1slu_8!@c1w@%)+_+dxy&'
else:
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')


ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_assets',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',

    'django_extensions',
    'django_nose',

    # the Indigo API
    'indigo_api',

    # the Indigo browser application
    'indigo_app',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'indigo.urls'

WSGI_APPLICATION = 'indigo.wsgi.application'

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# where does the pdftotext binary live?
if DEBUG:
   INDIGO_PDFTOTEXT = 'pdftotext'
else:
   # on heroku, use the bundled version at bin/pdftotext
   INDIGO_PDFTOTEXT = os.path.abspath(
         os.path.join(
            os.path.dirname(__file__),
            '..', 'bin', 'pdftotext'))

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

import dj_database_url
DATABASES = {
    'default': dj_database_url.config(default='postgres://bylaws:bylaws@localhost:5432/bylaws')
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Templates
TEMPLATE_DEBUG = DEBUG
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.csrf',
    'django.core.context_processors.tz',
)

#TEMPLATE_DIRS = (
#    os.path.join(BASE_DIR, 'templates'),
#)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

ASSETS_DEBUG = DEBUG
ASSETS_URL_EXPIRE = False
# by default, it will look for everything in the 'static' dir
# for each Django app

# where the compiled assets go
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# the URL for assets
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
   "django.contrib.staticfiles.finders.FileSystemFinder",
   "django.contrib.staticfiles.finders.AppDirectoriesFinder",
   "django_assets.finders.AssetsFinder"
)

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'


# REST
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
       'rest_framework.authentication.SessionAuthentication',
       'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        'rest_framework.permissions.AllowAny',
    ]
}


DEFAULT_FROM_EMAIL = 'greg@code4sa.org'
EMAIL_HOST = 'smtp.mandrillapp.com'
EMAIL_HOST_USER = 'greg@code4sa.org'
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
EMAIL_PORT = 587
EMAIL_SUBJECT_PREFIX = '[Indigo] '

# disable email in development
if DEBUG:
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'ERROR'
        },
        'indigo_api': {
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'django': {
            'level': 'INFO',
        }
    }
}
