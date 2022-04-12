.. configuration:

Configuration
=============

Some Indigo config options can be set using environment variables. Others are
`Django configuration options <https://docs.djangoproject.com/en/4.0/topics/settings/>`_ and must be set in your
``settings.py`` file.

Options that can be set using environment variables:

* ``AWS_ACCESS_KEY_ID``

  **Required for production.**
  The AWS access key ID for the account with write-access to the S3 bucket used for storing attachments.

* ``AWS_SECRET_ACCESS_KEY``

  **Required for production.**
  The AWS secret access key for the account with write-access to the S3 bucket used for storing attachments.

* ``AWS_S3_BUCKET``

  **Required for production.**
  The name of the S3 bucket for storing attachments.

* ``AWS_S3_HOST``

  The regional S3 endpoint to use. Optional. Default: ``s3-eu-west-1.amazonaws.com``

* ``DATABASE_URL``
  
  **Required.**
  The URL of the database to use, in the format: ``postgres://USER:PASSWORD@HOST:PORT/DBNAME``.

* ``DJANGO_DEBUG``
  
  The Django ``DEBUG`` setting.  Everything other than ``true`` means False.
  This should always be ``false`` in production. Default: ``true``

* ``DJANGO_DEFAULT_FROM_EMAIL``

  The Django ``DEFAULT_FROM_EMAIL`` setting: who do emails come from? Uses ``SUPPORT_EMAIL``
  by default.

* ``DJANGO_EMAIL_HOST``

  The Django ``EMAIL_HOST`` `setting <https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-EMAIL_HOST>`_.
  The SMTP host through which to send user emails such as password resets.

* ``DJANGO_EMAIL_HOST_PASSWORD``

  The Django ``EMAIL_HOST_PASSWORD`` `setting <https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-EMAIL_HOST_PASSWORD>`_.
  The SMTP password.

* ``DJANGO_EMAIL_HOST_PORT``

  The Django ``EMAIL_HOST_PORT`` `setting <https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-EMAIL_HOST_PORT>`_.
  The SMTP port (default: 25).

* ``DJANGO_EMAIL_HOST_USER``

  The Django ``EMAIL_HOST_USER`` `setting <https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-EMAIL_HOST_USER>`_.
  The SMTP username.

* ``DJANGO_SECRET_KEY``

  **Required if DJANGO_DEBUG is not true.**
  The Django ``SECRET_KEY`` `setting <https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-SECRET_KEY>`_. In production you should use a random (and secret) string.

* ``GOOGLE_ANALYTICS_ID``

  Google Analytics ID for website tracking. Only used when ``DEBUG`` is False.

* ``SUPPORT_EMAIL``

  **Required**
  Email address users can email for help.

* ``INDIGO.EMAIL_FAIL_SILENTLY``

  Should email sending fail silently?

* ``INDIGO.GSHEETS_API_CREDS``

  JSON of Google Sheets API credentials token details, if you want Indigo to be able to talk to Google Sheets directly. Otherwise,
  Indigo will use CSV export and the Google Sheet will need to be publicly accessible.

  For details on setting up Google Sheets for API access, see https://medium.com/@denisluiz/python-with-google-sheets-service-account-step-by-step-8f74c26ed28e

* ``INDIGO.NOTIFICATION_EMAILS_BACKGROUND``

  Should notification emails be sent asynchronously in the background? Default is False. See
  `django-background-tasks documentation <https://django-background-tasks.readthedocs.io/en/latest/>`_.

* ``INDIGO.PRUNE_DELETED_DOCUMENT_DAYS``

  If this is set, deleted documents older than the specified number of days will be deleted. Background tasks
  must be run to do so. Defaults to 90 days.

* ``INDIGO.PRUNE_DOCUMENT_VERSIONS_DAYS``

  If this is set, document versions older than the specified number of days will be deleted, except
  the ``INDIGO.PRUNE_DOCUMENT_VERSIONS_KEEP`` most recent. Defaults to 90 days.

* ``INDIGO.PRUNE_DOCUMENT_VERSIONS_KEEP``

  The number of recent document versions to keep when pruning document versions. Defaults to 5.

Options that must be set in your ``settings.py``:

* ``INDIGO.DOCTYPES``

  A list of ``(label, code)`` pairs of Akoma Ntoso document types that can be
  created, such as ``('Act', 'act')``. See http://docs.oasis-open.org/legaldocml/akn-core/v1.0/os/part1-vocabulary/akn-core-v1.0-os-part1-vocabulary.html#_Toc523925025
  
  Note that currently the Slaw parser only recognizes the 'act' doctype.

Authentication
--------------

Indigo uses `django-allauth <http://django-allauth.readthedocs.io/en/latest/index.html>`_ for user authentication and social accounts, configuration
is as per the django-allauth documentation.

Social Accounts
...............

By default, Indigo doesn't have any social account authentication enabled. To enable a social provider, follow the documentation for django-allauth. Namely, you'll need to:

1. Include the account provider in `INSTALLED_APPS` in your ``settings.py`` file::

   INSTALLED_APPS = INSTALLED_APPS + ('allauth.socialaccount.providers.google',)

2. Get the appropriate client and secret keys from the provider, and create a social app in the admin interface.
