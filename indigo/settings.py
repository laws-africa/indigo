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
    'reversion',
    'ckeditor',
    'corsheaders',
    'indigo_api',

    # the Indigo browser application
    'indigo_app',
    # the Indigo act resolver
    'indigo_resolver',
)

MIDDLEWARE = (
    #'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
    INDIGO_PDFTOTEXT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin', 'pdftotext'))

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

# CORS
CORS_ORIGIN_ALLOW_ALL = True


# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.csrf',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'indigo_app.context_processors.general',
            ]
        }
    }
]

# attachments
if not DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_FILE_OVERWRITE = False
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET')
    AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_HOST", "http://s3-eu-west-1.amazonaws.com")
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }


# Caches
if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        },
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '/var/tmp/django_cache',
        },
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
PIPELINE = {
    'STYLESHEETS': {
        'css': {
            'source_filenames': (
                'bower_components/bootstrap/dist/css/bootstrap.min.css',
                'bower_components/bootstrap/dist/css/bootstrap-theme.min.css',
                'bower_components/fontawesome/css/font-awesome.css',
                'bower_components/bootstrap-datepicker/css/datepicker3.css',
                'stylesheets/select2-4.0.0.min.css',
                'stylesheets/bootstrap-menus.scss',
                'stylesheets/app.scss',
            ),
            'output_filename': 'app.css',
        },
        'export': {
            'source_filenames': (
                # these are both in indigo_api/static/
                'stylesheets/bootstrap.min.css',
                'stylesheets/export.scss',
            ),
            'output_filename': 'export.css',
        },
        'epub': {
            'source_filenames': (
                # these are in indigo_api/static/
                'stylesheets/bootstrap.min.css',
                'stylesheets/export.scss',
                'stylesheets/epub.scss',
            ),
            'output_filename': 'epub.css',
        },
        'resolver': {
            'source_filenames': (
                'bower_components/bootstrap/dist/css/bootstrap.min.css',
                'stylesheets/resolver.scss',
            ),
            'output_filename': 'resolver.css',
        },
        'lime': {
            'source_filenames': (
                'lime/dist/resources/LIME-all.css',
                'lime/dist/resources/stylesheets/extjs4.editor.css',
                'lime/dist/resources/stylesheets/extjs4.viewport.css',
            ),
            'output_filename': 'lime.css',
        }
    },
    'JAVASCRIPT': {
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
                'javascript/select2-4.0.0.min.js',
                'javascript/caret.js',
                'javascript/prettyprint.js',
                'javascript/table-editor.js',
                'javascript/indigo/models.js',
                'javascript/indigo/views/user.js',
                'javascript/indigo/views/reset_password.js',
                'javascript/indigo/views/document_defined_terms.js',
                'javascript/indigo/views/document_references.js',
                'javascript/indigo/views/document_amendments.js',
                'javascript/indigo/views/document_repeal.js',
                'javascript/indigo/views/document_attachments.js',
                'javascript/indigo/views/document_properties.js',
                'javascript/indigo/views/document_chooser.js',
                'javascript/indigo/views/document_toc.js',
                'javascript/indigo/views/table_editor.js',
                'javascript/indigo/views/document_editor.js',
                'javascript/indigo/views/document_revisions.js',
                'javascript/indigo/views/document.js',
                'javascript/indigo/views/library.js',
                'javascript/indigo/views/error_box.js',
                'javascript/indigo/views/progress.js',
                'javascript/indigo/views/import.js',
                'javascript/indigo/views/annotations.js',
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
        },
        'resolver': {
            'source_filenames': (
                'bower_components/jquery/dist/jquery.min.js',
                'javascript/resolver.js',
            ),
            'output_filename': 'resolver.js',
        }
    },
    'CSS_COMPRESSOR': None,
    'JS_COMPRESSOR': None,
    # don't wrap javascript, this breaks LIME
    # see https://github.com/cyberdelia/django-pipeline/blob/ea74ea43ec6caeb4ec46cdeb7d7d70598e64ad1d/pipeline/compressors/__init__.py#L62
    'DISABLE_WRAPPER': True,
    'COMPILERS': [
        'indigo.pipeline.PyScssCompiler',
    ],
    'PIPELINE_ENABLED': not DEBUG,
    'PIPELINE_COLLECTOR_ENABLED': True,
}

PYSCSS_LOAD_PATHS = [
    os.path.join(BASE_DIR, 'indigo_api', 'static'),
    os.path.join(BASE_DIR, 'indigo_app', 'static'),
    os.path.join(BASE_DIR, 'indigo_resolver', 'static'),
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

# Django Rest Auth
REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER': 'indigo_app.serializers.UserDetailsSerializer',
}


SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL')

DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', SUPPORT_EMAIL)
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', 25))
EMAIL_SUBJECT_PREFIX = '[Indigo] '


INDIGO_ORGANISATION = os.environ.get('INDIGO_ORGANISATION', 'Indigo Platform')
INDIGO_URL = os.environ.get('INDIGO_URL', 'https://indigo.code4sa.org')
RESOLVER_URL = os.environ.get('RESOLVER_URL', INDIGO_URL + "/resolver/resolve")

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID')
# server-side google analytics
GOOGLE_ANALYTICS_INCLUDE_PATH = ['/api/']
if GOOGLE_ANALYTICS_ID and not DEBUG:
    MIDDLEWARE += ('indigo.middleware.GoogleAnalyticsMiddleware',)

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
        'django.template': {
            'level': 'INFO',
        },
    }
}
