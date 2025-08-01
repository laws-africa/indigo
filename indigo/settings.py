"""
Django settings for indigo project.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
import logging
from urllib.parse import urlparse

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from .version import __version__

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


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
    # Indigo local traditions
    'indigo_za',

    # Indigo social
    'indigo_social',

    # the Indigo act resolver
    'indigo_resolver',

    # the Indigo editor application
    'indigo_app',
    # the Indigo published content API
    'indigo_content_api',
    # the Indigo API
    'indigo_api',

    # base indigo installation
    'indigo',

    'background_task',
    'actstream',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # installations should include social account providers, such as
    # allauth.socialaccount.providers.google
    'django_recaptcha',

    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'sass_processor',
    'pipeline',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'treebeard',

    # required by the Indigo API
    'countries_plus',
    'languages_plus',
    'storages',
    'reversion',
    'ckeditor',
    'corsheaders',

    # required for commenting on tasks
    'django_comments',

    'django_htmx',
    'drf_spectacular',
)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'indigo_app.middleware.VaryOnHxHeadersMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'indigo_app.middleware.HtmxMessagesMiddleware',
)

ROOT_URLCONF = 'indigo.urls'

WSGI_APPLICATION = 'indigo.wsgi.application'

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_SECURE = not DEBUG

# where does the pdftotext binary live?
INDIGO_PDFTOTEXT = 'pdftotext'
# TODO move all Indigo config options in here
INDIGO = {
    # Should we send notification emails in the background?
    # Requires a separate task runner for django-background-tasks,
    # see https://django-background-tasks.readthedocs.io/en/latest/
    'NOTIFICATION_EMAILS_BACKGROUND': False,

    # If an email fails to send, should we raise an exception?
    'EMAIL_FAIL_SILENTLY': False,

    # permanently delete documents deleted this many days ago. Set to 0 to disable.
    'PRUNE_DELETED_DOCUMENT_DAYS': 90,
    # delete document versions older than this...
    'PRUNE_DOCUMENT_VERSIONS_DAYS': 90,
    # ... but keep this number of most recent ones
    'PRUNE_DOCUMENT_VERSIONS_KEEP': 5,

    # Key-value pairs for custom properties, per place code.
    'WORK_PROPERTIES': {},

    # maximum number of tasks that can be assigned to a user at a time
    'MAX_ASSIGNED_TASKS': 999999,

    # AKN document types the platform supports, as a list of (name, code) tuples
    # see http://docs.oasis-open.org/legaldocml/akn-core/v1.0/os/part1-vocabulary/akn-core-v1.0-os-part1-vocabulary.html#_Toc523925025
    'DOCTYPES': [('Act', 'act'), ('Statement', 'statement')],
    'EXTRA_DOCTYPES': {},

    # disable entire site except for superusers and the content API
    'MAINTENANCE_MODE': bool(os.environ.get("INDIGO_MAINTENANCE_MODE")),

    'CONTENT_API': {
        # URL prefix for where the API is mounted
        'API_PREFIX': 'api/',
        # django URL files to include for each API version
        'URLCONF': {
            'v2': 'indigo_content_api.v2.urls_api',
            'v3': 'indigo_content_api.v3.urls_api',
        }
    },

    # namespaces to look for translation packs for javascript translation via i18next
    'JS_I18N_NAMESPACES': ['indigo_app'],

    # Plugins to use for linking references. The internal-refs must come after work-level plugins.
    'LINK_REFERENCES_PLUGINS': [
        'refs-act-numbers', 'refs-act-names', 'refs-subtype-numbers', 'refs-aliases', 'internal-refs'
    ],

    # should we use pyodide to parse documents on the client?
    'USE_PYODIDE': True,
}

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

import dj_database_url
db_config = dj_database_url.config(default='postgres://indigo:indigo@localhost:5432/indigo')
db_config['ATOMIC_REQUESTS'] = True
DATABASES = {
    'default': db_config,
}
CONN_MAX_AGE = int(os.environ.get('CONN_MAX_AGE', 0))

# Auto-created primary keys
# see: https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

SITE_ID = 1

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
]
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
                'indigo_app.context_processors.models',
            ]
        }
    }
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "indigo.pipeline.GzipManifestPipelineStorage"
    }
}

# attachments
if not DEBUG:
    STORAGES["default"]["BACKEND"] = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_FILE_OVERWRITE = False
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET')
    AWS_S3_REGION_NAME = 'eu-west-1'
    AWS_DEFAULT_ACL = None
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
# https://docs.djangoproject.com/en/3.2/howto/static-files/

ASSETS_DEBUG = DEBUG
ASSETS_URL_EXPIRE = False
# by default, it will look for everything in the 'static' dir
# for each Django app

# where the compiled assets go
STATIC_ROOT = os.path.join(os.getcwd(), 'staticfiles')
# the URL for assets
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
    "pipeline.finders.PipelineFinder",
)

if os.environ.get("NODE_PATH"):
    SASS_PROCESSOR_INCLUDE_DIRS = [os.environ.get("NODE_PATH")]
else:
    # look for node modules in the current dir, and in the project root
    SASS_PROCESSOR_INCLUDE_DIRS = [
        os.path.join(".", "node_modules"),
        os.path.join(BASE_DIR, "node_modules"),
    ]

# supplement whitenoise's mimetypes
WHITENOISE_MIMETYPES = {
    '.xsl': 'application/xslt+xml',
    '.xslt': 'application/xslt+xml',
}


# django-pipeline for javascript
PIPELINE = {
    'JAVASCRIPT': {
        'js': {
            'source_filenames': (
                'lib/external-imports.js',
                'bower_components/jquery/dist/jquery.min.js',
                'bower_components/jquery-cookie/jquery.cookie.js',
                'bower_components/underscore/underscore-min.js',
                'bower_components/backbone/backbone.js',
                'bower_components/backbone.stickit/backbone.stickit.js',
                'lib/bootstrap-select/js/bootstrap-select.min.js',
                'bower_components/handlebars/handlebars.min.js',
                'bower_components/moment/min/moment.min.js',
                'bower_components/moment/locale/en-gb.js',
                'javascript/select2-4.0.0.min.js',
                'javascript/caret.js',
                'javascript/prettyprint.js',
                'javascript/table-editor.js',
                'javascript/indigo/models.js',
                'javascript/indigo/traditions.js',
                'javascript/indigo/*.js',
                'javascript/indigo/views/*.js',
                'javascript/indigo/views/**/*.js',
                'javascript/indigo/**/*.js',
                'javascript/indigo.js',
            ),
            'output_filename': 'app.js',
        },
        'resolver': {
            'source_filenames': (
                'bower_components/jquery/dist/jquery.min.js',
                'javascript/resolver.js',
            ),
            'output_filename': 'resolver.js',
        }
    },
    'JS_COMPRESSOR': None,
    # don't wrap javascript, this breaks LIME
    # see https://github.com/cyberdelia/django-pipeline/blob/ea74ea43ec6caeb4ec46cdeb7d7d70598e64ad1d/pipeline/compressors/__init__.py#L62
    'DISABLE_WRAPPER': True,
    'PIPELINE_ENABLED': not DEBUG,
    'PIPELINE_COLLECTOR_ENABLED': True,
}


# SSL indicator from the nginx proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

X_FRAME_OPTIONS = 'SAMEORIGIN'


# REST
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_PAGINATION_CLASS': 'indigo_api.utils.PageNumberPagination',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL')
INDIGO_ORGANISATION = os.environ.get('INDIGO_ORGANISATION', 'Indigo Platform')
INDIGO_URL = os.environ.get('INDIGO_URL', 'http://localhost:8000')
INDIGO_USER_PROFILE_URL = 'indigo_social:user_profile'
RESOLVER_URL = os.environ.get('RESOLVER_URL', INDIGO_URL + "/resolver/resolve")

INDIGO_SOCIAL = {
    # the badge module to load by default (optional)
    'badges': 'indigo_social.default_badges',
    # when a user signs up, grant them these badges automatically
    'new_user_badges': ['contributor'],
}

SPECTACULAR_SETTINGS = {
    "TITLE": f'{INDIGO_ORGANISATION} Content API',
    "VERSION": __version__,
    "DESCRIPTION": "Read-only Content API",
}

SERVER_EMAIL = DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', '%s <%s>' % (INDIGO_ORGANISATION, SUPPORT_EMAIL))
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', 25))
EMAIL_USE_TLS = os.environ.get('DJANGO_EMAIL_USE_TLS', 'false') == 'true'
EMAIL_USE_SSL = os.environ.get('DJANGO_EMAIL_USE_SSL', 'false') == 'true'
EMAIL_SUBJECT_PREFIX = '[%s] ' % INDIGO_ORGANISATION

# Auth
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Django all-auth settings
ACCOUNT_ADAPTER = 'indigo_app.adapter.ModifiedAccountAdapter'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = EMAIL_SUBJECT_PREFIX
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/accounts/email/'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_DISPLAY = 'indigo_api.serializers.user_display_name'
ACCOUNT_FORMS = {
    'signup': 'indigo_app.forms.UserSignupForm'
}
ACCOUNT_SIGNUP_ENABLED = True
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = '/places'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Google recaptcha
RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')
if DEBUG:
    # don't complain about the test keys
    SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']


DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID')

# disable email in development
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.INFO: 'alert alert-primary auto-dismiss',
    messages.SUCCESS: 'alert alert-success auto-dismiss',
    messages.WARNING: 'alert alert-warning',
    messages.ERROR: 'alert alert-danger',
}


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
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'ERROR'
        },
        'indigo': {
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'indigo.plugins': {
            'level': 'INFO',
        },
        'indigo.analysis': {
            'level': 'INFO',
        },
        'indigo_api.utils': {
            'level': 'INFO',
        },
        'indigo_lib': {
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'indigo.tasks': {
            'handlers': [] if DEBUG else ['mail_admins'],
            'level': 'INFO',
        },
        'indigo_api': {
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'indigo_app': {
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'indigo_metrics': {
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'django': {
            'level': 'INFO',
        },
        'django.template': {
            'level': 'INFO',
        },
        'django.request': {
            'handlers': [] if DEBUG else ['mail_admins'],
            'level': 'ERROR',
        },
    }
}

# Activity stream
ACTSTREAM_SETTINGS = {
    'USE_JSONFIELD': True,
}

# Adminstrators intended to receive email notifications
# Each item in the list should be a tuple of (Full name, email address). Example:
# [('Indigo Admin', 'indigoadmin@example.com')]
ADMINS = []

# Sentry configuration
SENTRY_DSN = os.environ.get('SENTRY_DSN')

# Sample 50% of requests for performance metrics by default or use the configured
# environment variable which is a number between 0 (0% of errors sent) and 1 (100% of errors sent).
SENTRY_SAMPLE_RATE = float(os.environ.get('SENTRY_SAMPLE_RATE', 0.5))

if not DEBUG and SENTRY_DSN:
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=None,  # Don't send errors based on log messages
    )

    def exclude_static(event, hint):
        # don't set /static to Sentry, to avoid using up quota
        if "request" in event and event["request"].get("url"):
            url = urlparse(event["request"]["url"])
            if url.path.startswith("/static/"):
                return None
        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), sentry_logging],
        send_default_pii=True,
        traces_sample_rate=SENTRY_SAMPLE_RATE,
        before_send_transaction=exclude_static,
        _experiments={
            "profiles_sample_rate": 1.0,
        },
    )

# where does the fop binary live?
FOP_CMD = os.environ.get("FOP_CMD", "fop")
FOP_CONFIG = os.environ.get("FOP_CONFIG")
FOP_FONT_PATH = os.environ.get("FOP_FONT_PATH")

# allow injection of a custom test runner for github actions
TEST_RUNNER = os.environ.get('TEST_RUNNER', 'django.test.runner.DiscoverRunner')
# only used by xmlrunner https://github.com/xmlrunner/unittest-xml-reporting#django-support
TEST_OUTPUT_DIR = './test-reports'
