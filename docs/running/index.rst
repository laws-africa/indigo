.. running:

Installing and Running Indigo
=============================

This guide is for developers who want to install and run their own instance
of the Indigo platform.

Indigo is a Django web application that is easily deployed on
`Heroku <https://heroku.com/>`_ or `Dokku <http://progrium.viewdocs.io/dokku/>`_.
Dokku emulates a Heroku-like environment on your own servers (or cloud).

.. note::

    We recommend using Dokku for production because some Indigo functionality
    -- such as parsing new documents -- can take longer than the 30 seconds
    Heroku allows for web API calls. However, Heroku is great for quickly trying Indigo
    out.

Requirements
------------

Indigo requires:

* Python 2.7.8
* Postgresql 9.3+
* Ruby 2.1.6+ for `Slaw <https://github.com/longhotsummer/slaw>`_
* Java 1.8 for `Apache Tika <https://tika.apache.org/>`_
* An AWS S3 account and bucket for storing attachments

Optional but useful:

* A `New Relic <http://newrelic.com>`_ monitoring account
* An SMTP server to send email through, or a service like `Mandrill <https://mandrillapp.com/>`_

Using Heroku/Dokku means that we're using well-document and widely understood
mechanisms for specifying dependencies and configuration across multiple
languages. It takes care of all this for you and we highly recommend using them.

Installation
------------

Installation on Heroku and Dokku are similar and only really differ in the commands that are run.
We describe using Heroku below.

1. Create a new AWS S3 account and bucket for storing attachments. You'll need the AWS Access Key Id and AWS Secret Access Key later.
2. Clone the repo::
   
    $ git clone https://github.com/Code4SA/indigo
    $ cd indigo

3. Create a new Heroku application::

    $ heroku apps:create indigo

4. Create a Postgres database::

    $ heroku addons:create heroku-postgresql

5. Set config options::

    $ heroku config:set indigo \
        DISABLE_COLLECTSTATIC=1 \
        DJANGO_DEBUG=false \
        DJANGO_SECRET_KEY=some random characters \
        AWS_ACCESS_KEY_ID=aws access key \
        AWS_SECRET_ACCESS_KEY=aws secret access key \
        AWS_S3_BUCKET=your-bucket-name

6. If you're using New Relic, you'll need to set those config options::

    $ heroku config:set indigo \
        NEW_RELIC_APP_NAME=Indigo \
        NEW_RELIC_LICENSE_KEY=7e4b428f9f46d4b3a943a3577e636337f35e5ec4

7. Deploy::

    $ git push heroku

8. Setup the Indigo database::

    $ heroku run python manage.py migrate

9. Create the admin user::

    $ heroku run python manage.py createsuperuser

10. Visit your new Indigo app in your browser!

11. You can configure new users and other things at `/admin`.

TODO:

* document configuring country details

Configuration
-------------

Config options are mostly passed to Indigo as environment variables. These are the options you can set:

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
  The URL of the database to use

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

* ``NEW_RELIC_APP_NAME``

  The New Relic App Name, if you're using New Relic.

* ``NEW_RELIC_LICENSE_KEY``

  The New Relic license key, if you're using New Relic.

* ``SUPPORT_EMAIL``

  **Required**
  Email address users can email for help.
