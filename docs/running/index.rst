.. running:

Installing and Running Indigo
=============================

This guide is for developers who want to install and run their own instance
of the Indigo platform.

Indigo is a Django web application that can be run as a standalone project, or
as part of an existing Django project. This guide will explain how to run Indigo as
a standalone project.

Indigo requires some non-python dependencies. This guide explains how to deploy
Indigo and these dependencies on `Heroku <https://heroku.com/>`_ or `Dokku <http://progrium.viewdocs.io/dokku/>`_.
Dokku emulates a Heroku-like environment on your own servers (or cloud).

.. note::

    We recommend using Dokku for production because some Indigo functionality
    -- such as parsing new documents -- can take longer than the 30 seconds
    Heroku allows for web API calls. However, Heroku is great for quickly trying Indigo
    out.

Requirements
------------

Indigo requires:

* Python 2.7
* Postgresql 9.3+
* Ruby 2.1.6+ for `Slaw <https://github.com/longhotsummer/slaw>`_
* Java 1.8 for `Apache Tika <https://tika.apache.org/>`_
* An AWS S3 account and bucket for storing attachments

Optional but useful:

* An SMTP server to send email through, or an appropriate service

Using Heroku/Dokku means that we're using well-document and widely understood
mechanisms for specifying dependencies and configuration across multiple
languages. It takes care of all this for you and we highly recommend using them.

Local Installation
------------------

Installation on Heroku and Dokku are similar and only really differ in the commands that are run.
We describe using Heroku below.

1. Install pipenv according to the instructions: `pipenv <https://docs.pipenv.org/>`_
2. Clone the `github.com/OpenUpSA/example-indigo <https://github.com/OpenUpSA/example-indigo>`_ repository. It has all Indigo's dependencies for Python, Ruby and Java described in it::

    $ git clone https://github.com/OpenUpSA/example-indigo
    $ cd indigo

3. Activate the virtual environment and install python dependencies::

    $ pipenv install

4. Ensure you have PostgreSQL installed and running. Create a postgresql user with username and password indigo, and create a corresponding database called indigo::

    $ sudo su - postgres -c 'createuser -d -P indigo'
    $ sudo su - postgres -c 'createdb indigo'

5. Run the migrations to setup the initial database::

    $ pipenv run python manage.py migrate
    $ pipenv run python manage.py update_countries_plus

6. Then create the superuser::

    $ pipenv run python manage.py createsuperuser

7. Finally, run the server::

    pipenv run python manage.py runserver

8. And visit the website to login: http://localhost:8000/

9. You can visit the admin interface to add your own country details and create new users: http://localhost:8000/admin

Ruby dependencies
=================

You won't be able to import documents yet. First, you'll need to install Ruby and the Slaw parser library. We strongly recommend installing and using RVM or a similar Ruby version manager. You'll need Ruby version 2.3.

Once you've install Ruby, install Bundler and the Indigo dependencies::

    $ gem install bundler
    $ bundle install

You can test that Slaw is installed with slaw --version::

    $ slaw --version
    slaw 1.0.1

Django Customisation
====================

You can now easily change Django settings, add your own modules, change URLs, etc. You simply need to create your own settings file, import the settings from Indigo, and update `manage.py` to reference your new settings file. For example:

1. Create a python module folder `my_app`::

    $ mkdir my_app; touch my_app/__init__.py

2. Create `my_app/settings.py` so that it looks like this::

    from indigo.settings import *

    # override any Django settings, as you would normally.

    # add your own apps, eg:
    # INSTALLED_APPS = ('my_app',) + INSTALLED_APPS

    # add your own URLs
    # ROOT_URLCONF = 'my_app.urls'

    # etc.

3. Update `manage.py` so that it references your new `my_app.settings` file::

    #!/usr/bin/env python
    import os
    import sys

    if __name__ == "__main__":
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_app.settings")

        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)

4. Run your updated app with ``pipenv run python manage.py runserver``

Production Installation
-----------------------

3. Create a new Heroku application::

    $ heroku apps:create indigo

4. Create a Postgres database::

    $ heroku addons:create heroku-postgresql

5. (optional) Create a new AWS S3 account and bucket for storing attachments. You'll need the AWS Access Key Id and AWS Secret Access Key in the next step. You can safely skip this step if you don't care about saving attachments just yet.

5. Set config options::

    $ heroku config:set indigo \
        DISABLE_COLLECTSTATIC=1 \
        DJANGO_DEBUG=false \
        DJANGO_SECRET_KEY=some random characters \
        AWS_ACCESS_KEY_ID=aws access key \
        AWS_SECRET_ACCESS_KEY=aws secret access key \
        AWS_S3_BUCKET=your-bucket-name

7. Deploy::

    $ git push heroku

8. Setup the Indigo database::

    $ heroku run python manage.py migrate

9. Create the admin user::

    $ heroku run python manage.py createsuperuser

10. Visit your new Indigo app in your browser!

11. You can configure new users and other things at `/admin`.

12. You'll need to set some :ref:`permissions` for users.


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

* ``SUPPORT_EMAIL``

  **Required**
  Email address users can email for help.
