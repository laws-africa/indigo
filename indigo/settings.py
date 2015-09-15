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
    'pipeline',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    'django_extensions',
    'django_nose',

    # the Indigo API
    'taggit',
    'taggit_serializer',
    'countries_plus',
    'languages_plus',
    'storages',
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

# LIME editor
# We use the compiled version of the LIME editor in production and, by default, development.
# Set this to True to use the development version in development.
INDIGO_LIME_DEBUG = False

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

import dj_database_url
db_config = dj_database_url.config(default='postgres://indigo:indigo@localhost:5432/indigo')
db_config['ATOMIC_REQUESTS'] = False
DATABASES = {
    'default': db_config,
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
    'indigo_app.context_processors.general',
)

# attachments
if not DEBUG:
    DEFAULT_FILE_STORAGE = 'indigo.botopatch.S3Storage'
    AWS_S3_FILE_OVERWRITE = False
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET')
    AWS_S3_HOST = os.environ.get("AWS_S3_HOST", "s3-eu-west-1.amazonaws.com")
    AWS_HEADERS = {
        'Cache-Control': 'max-age=86400',
    }


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
    "pipeline.finders.PipelineFinder",
)

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = 'indigo.pipeline.GzipManifestPipelineStorage'


# django-pipeline and pyscss settings

PIPELINE_CSS = {
    'css': {
        'source_filenames': (
            'bower_components/bootstrap/dist/css/bootstrap.min.css',
            'bower_components/bootstrap/dist/css/bootstrap-theme.min.css',
            'bower_components/fontawesome/css/font-awesome.css',
            'bower_components/bootstrap-datepicker/css/datepicker3.css',
            'stylesheets/select2-4.0.0.min.css',
            'stylesheets/app.scss',
        ),
        'output_filename': 'app.css',
    },
    'lime': {
        'source_filenames': (
            'lime/dist/resources/LIME-all.css',
            'lime/dist/resources/stylesheets/extjs4.editor.css',
            'lime/dist/resources/stylesheets/extjs4.viewport.css',
        ),
        'output_filename': 'lime.css',
    }
}
PIPELINE_JS = {
    'js': {
        'source_filenames': (
            'bower_components/jquery/dist/jquery.min.js',
            'bower_components/jquery-cookie/jquery.cookie.js',
            'bower_components/underscore/underscore-min.js',
            'bower_components/backbone/backbone.js',
            'bower_components/backbone.stickit/backbone.stickit.js',
            'bower_components/bootstrap/dist/js/bootstrap.min.js',
            'bower_components/handlebars/handlebars.min.js',
            'bower_components/moment/min/moment.min.js',
            'bower_components/moment/locale/en-gb.js',
            'bower_components/bootstrap-datepicker/js/bootstrap-datepicker.js',
            'bower_components/tablesorter/jquery.tablesorter.min.js',
            'javascript/select2-4.0.0.min.js',
            'javascript/caret.js',
            'javascript/prettyprint.js',
            'javascript/indigo/models.js',
            'javascript/indigo/views/user.js',
            'javascript/indigo/views/reset_password.js',
            'javascript/indigo/views/document_amendments.js',
            'javascript/indigo/views/document_repeal.js',
            'javascript/indigo/views/document_attachments.js',
            'javascript/indigo/views/document_analysis.js',
            'javascript/indigo/views/document_properties.js',
            'javascript/indigo/views/document_chooser.js',
            'javascript/indigo/views/document_toc.js',
            'javascript/indigo/views/document_editor.js',
            'javascript/indigo/views/document.js',
            'javascript/indigo/views/library.js',
            'javascript/indigo/views/error_box.js',
            'javascript/indigo/views/import.js',
            'javascript/indigo/timestamps.js',
            'javascript/indigo.js',
        ),
        'output_filename': 'app.js',
    },
    'lime': {
        'source_filenames': (
            'lime/dist/app.js',
            'javascript/lime-post.js'
        ),
        'output_filename': 'lime-bootstrap.js',
    }
}

PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = None
# don't wrap javascript, this breaks LIME
# see https://github.com/cyberdelia/django-pipeline/blob/ea74ea43ec6caeb4ec46cdeb7d7d70598e64ad1d/pipeline/compressors/__init__.py#L62
PIPELINE_DISABLE_WRAPPER = True
PIPELINE_COMPILERS = (
    'indigo.pipeline.PyScssCompiler',
)

PYSCSS_LOAD_PATHS = [
    os.path.join(BASE_DIR, 'indigo_app', 'static'),
    os.path.join(BASE_DIR, 'indigo_app', 'static', 'bower_components'),
]


# REST
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        'rest_framework.permissions.AllowAny',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'PAGE_SIZE': 250,
}

SUPPORT_EMAIL = 'mariyab@africanlii.org'

DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL')
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', 25))
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
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
    }
}
