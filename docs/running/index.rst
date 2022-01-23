.. running:

Installing and Running Indigo
=============================

This guide is for developers who want to install and run their own instance
of the Indigo platform.

Indigo is a Django web application that can be run as a standalone project, or
as part of an existing Django project. This guide will explain how to run Indigo as
a standalone project.

Requirements
------------

Indigo requires:

* Python 3.8+
* PostgreSQL 9.3+
* Ruby 2.7.0+ for `Slaw <https://github.com/longhotsummer/slaw>`_
* An AWS S3 account and bucket for storing attachments
* `wkhtmltopdf <https://wkhtmltopdf.org/>`_ for generating PDFs
* `pdftotext <https://poppler.freedesktop.org/>`_ for reading PDFs

Optional but useful:

* An SMTP server to send email through, or an appropriate service

Using Heroku/Dokku means that we're using well-document and widely understood
mechanisms for specifying dependencies and configuration across multiple
languages. It takes care of all this for you and we highly recommend using them.

Installing Indigo Locally
-------------------------

1. Ensure you have Python 3.6+ installed
2. Clone the `github.com/laws-africa/example-indigo <https://github.com/laws-africa/example-indigo>`_ repository. It has all Indigo's dependencies for Python and Ruby described in it::

    $ git clone https://github.com/laws-africa/example-indigo
    $ cd indigo

3. Setup and activate the virtual environment::

    $ python3 -m venv env
    $ source env/bin/activate

4. Install Python dependencies::

    $ pip install -r requirements.txt

5. Ensure you have PostgreSQL installed and running. Create a postgresql user with username and password `indigo`, and create a corresponding database called `indigo`::

    $ sudo su - postgres -c 'createuser -d -P indigo'
    $ sudo su - postgres -c 'createdb indigo'

6. Run the Django database migrations to setup the initial database::

    $ python manage.py migrate
    $ python manage.py update_countries_plus
    $ python manage.py loaddata languages_data.json.gz

7. Then create the superuser::

    $ python manage.py createsuperuser

8. Finally, run the server::

    $ python manage.py runserver

9. Visit the website to login: http://localhost:8000/

10. Configure a language and a country:

   * Visit http://localhost:8000/admin
   * Under **Indigo API** click Languages, then click Add Language in the top right corner
   * Choose a language from the dropdown list and click Save
   * Under **Indigo API** click Countries, then click Add Country in the top right corner
   * Choose a country and primary language from the dropdown lists
   * Click Save

11. Now go back to http://localhost:8000/ and your country will be included in the list.

Ruby dependencies
.................

You won't be able to import documents yet. First, you'll need to install Ruby and the Slaw parser library. We strongly recommend installing and using RVM or a similar Ruby version manager. You'll need at least Ruby version 2.6.

Once you've install Ruby, install Bundler and the Indigo dependencies::

    $ gem install bundler
    $ bundle install

You can test that Slaw is installed::

    $ slaw --version
    slaw 10.6.0

PDF support
...........

Indigo creates PDF files using `wkhtmltopdf <https://wkhtmltopdf.org/>`_. Install it as appropriate for your platform.

Indigo reads from PDF files using pdftotext, which is part of the `poppler-utils <https://poppler.freedesktop.org/>`_ package. Install it as appropriate for your platform.

Django Customisation
....................

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

4. Run your updated app with ``python manage.py runserver``

Production Installation
-----------------------

Indigo requires some non-Python dependencies. This guide explains how to deploy on either Dokku (Simpler) or on a Debian 11 based VM, Container or Bare Metal:


Dokku Deployment
----------------

Indigo and these dependencies on `Heroku <https://heroku.com/>`_ or `Dokku <http://progrium.viewdocs.io/dokku/>`_.
Dokku uses Docker to emulate a Heroku-like environment on your own servers (or cloud).

.. note::

    We don't recommend using Heroku for production because some Indigo functionality
    -- such as parsing new documents -- can take longer than the 30 seconds
    Heroku allows for web API calls. However, Heroku is great for quickly trying Indigo
    out.

Installation on Heroku and Dokku are similar and only really differ in the commands that are run.
We describe using Dokku below, and assume that you have already have `Dokku installed <http://dokku.viewdocs.io/dokku/getting-started/installation/>`_.

1. Use the Dokku PostgreSQL plugin to create a database::

    $ sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git
    $ dokku postgres:create indigodb

2. Create a new Dokku application and link the postgres database to the application::

    $ dokku apps:create indigo
    $ dokku postgres:link indigodb indigo

3. (optional) Create a new AWS S3 account and bucket for storing attachments. You'll need the AWS Access Key Id and AWS Secret Access Key in the next step. You can safely skip this step if you don't care about saving attachments just yet. If you decide to skip this step, delete the trailing backslash (\) after the DJANGO_SECRET_KEY variable in step 4 and ignore the last three lines.

4. Set config options as follows (ensure you enter your correct database and AWS settings)::

    $ dokku config:set indigo \
        DISABLE_COLLECTSTATIC=1 \
        DJANGO_DEBUG=false \
        DJANGO_SECRET_KEY=some random characters \
        AWS_ACCESS_KEY_ID=aws access key \
        AWS_SECRET_ACCESS_KEY=aws secret access key \
        AWS_S3_BUCKET=your-bucket-name

5. Deploying requires using `git push` to push to dokku. So you'll need to add `dokku` as a git remote on your local host. If you have cloned the `example-indigo` repo from above, you can do the following (substitute the fqdn or IP address of the dokku host, or use localhost if you are deploying to a local Dokku instance)::

    $ git remote add dokku dokku@DOKKU-HOSTNAME:indigo

6. Disable HOSTS check for first deployment as this will cause a failure::

    $ dokku checks:disable indigo

7. Now deploy to dokku using `git push dokku`. This is how you deploy any and all updates::

    $ git push dokku

8. Create the an admin user by running this command **on the Dokku server**::

    $ dokku run indigo python manage.py createsuperuser

9. Install countries and languages::

    $ dokku run indigo python manage.py update_countries_plus
    $ dokku run indigo python manage.py loaddata languages_data.json.gz

10. Enable HOSTS check for future updates and ensuring post-deployment checks::

    $ dokku checks:enable indigo

11. Visit your new Indigo app in your browser at http://indigo.domain.com or http://indigo.host.domain.com (depending on how your Dokku installation was configured using the dokku domains:set-global command; read the `Dokku Getting Started documentation <https://dokku.com/docs/getting-started/installation/#2-optionally-connect-a-domain-to-your-server>` for details).

12. Configure a country:

   * Visit `http://your-dokku-host.example.com/admin`
   * Under **Indigo API** click Countries, then click Add Country in the top right corner
   * Choose a country and primary language from the dropdown lists
   * Click Save
   
Debian 11 VM, Container or Bare-metal
-------------------------------------

As this deployment is intended for an LXC Container running as root, you might need to create a sudo user and run the installation in that userspace if you are deploying this on bare-metal. The following instructions are run as root and tested on an updated Debian 11 LXC container.

This deployment can run directly from the IP address, however has been set to reduced security as it is recommended you run it behind an NginX reverse Proxy. Read the Gunicorn documentation for more information on this.

1. Install some required packages::

    # apt update && apt install git curl libssl-dev libreadline-dev zlib1g-dev autoconf bison build-essential libyaml-dev libreadline-dev libncurses5-dev libffi-dev libgdbm-dev xfonts-base xfonts-75dpi fontconfig xfonts-encodings xfonts-utils poppler-utils postgresql python3-pip libpq-dev libpoppler-dev sqlite3 libsqlite3-dev libbz2-dev wkhtmltopdf --no-install-recommends -y
    
2. Install Rbenv Ruby Version Manager so you can ensure that you run the correct Ruby version, this will also configure the necessary ENV variables for Ruby::

    # curl -fsSL https://github.com/rbenv/rbenv-installer/raw/HEAD/bin/rbenv-installer | bash
    # echo 'export PATH="$HOME/.rbenv/bin:$PATH"' >> ~/.bashrc
    # echo 'eval "$(rbenv init -)"' >> ~/.bashrc
    # source ~/.bashrc
    
   You can test if Rbenv correctly installed with the following command::
    
    # rbenv -v
    
   Now install the appropriate ruby version (2.7.2 at time of writing)::
    
    # rbenv install 2.7.2
  
   Set the global Ruby version to be used (Note, if you are deploying to bare-metal, this is not recommended as it might break other services)::
    
    # rbenv global 2.7.2
    
   You can test if this worked as follows (Which should return version 2.7.2)::
    
    # ruby -v

3. Install Pyenv Python Version Manager so you can ensure that you run the correct Python version, this will also configure the necessary ENV variables for Python::

    # curl https://pyenv.run | bash
    # echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    # echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    # echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
    # source ~/.bashrc
    
   You can test if Pyenv correctly installed with the following command::
    
    # pyenv -v
    
   Now install the appropriate ruby version (3.8.12 at time of writing)::
    
    # pyenv install 3.8.12

   Set the global Python version to be used (Note, if you are deploying to bare-metal, this is not recommended as it might break other services)::
    
    # pyenv global 3.8.12
    
   You can test if this worked as follows (Which should return version 3.8.12)::
    
    # python --version
    
4. Install some PyPi packages that you will need for a production deployment::

    # pip install --upgrade pip
    # pip install wheel
    # pip install -U pip setuptools
    # pip install gevent==21.8.0
    # pip install gunicorn==20.1.0
    # pip install psycopg2==2.8.6
    
5. Clone into the current version of Indigo::
 
    # git clone https://github.com/laws-africa/indigo
    # cd indigo
    
   Note: From here on, all commands will be run from this folder.
    
6. Setup the Indigo requirements::
 
    # pip install -e .
    
7. Configure the Postgres Database:
    
   Note that if you want to use a more secure configuration, you will need to edit the settings.py file contained in ./indigo/settings.py, the relevant variable is: db_config = dj_database_url.config(default='postgres://indigo:indigo@localhost:5432/indigo'). You can edit this if you use a different Postgres host, username or password than those set below::
    
    # su - postgres -c 'createuser -d -P indigo'
    
   Set the password to indigo unless you have changed settings.py, in which case, use that password::
    
    # su - postgres -c 'createdb indigo'
    
8. Install the Ruby gems required by Indigo::
 
    # gem install bundler
    # bundle install
 
9. Set some ENV variables in Debian required for Indigo to work in production mode::
 
    # nano ~/.bashrc
    
   Add the following lines to the bottom of the file, editing the portions in brackets (without brackets) as per your environment (i.e. DJANGO_SECRET_KEY=123456789, not DJANGO_SECRET_KEY={123456789}):
    
   Note, we set DJANGO_DEBUG=true for now, this is due to the way in which Django works and it cannot populate the database otherwise, as soon as we have run the first migration, we will change this::
    
    export DJANGO_DEBUG=true
    export DJANGO_SECRET_KEY={Some random characters}
    export AWS_ACCESS_KEY_ID={Your AWS Acces Key}
    export AWS_SECRET_ACCESS_KEY={Your AWS Secret Key}
    export AWS_S3_BUCKET={Your Amazon S3 Bucket Name, note, must be in eu-west-1}
    export SUPPORT_EMAIL={you@yourdomain.com}
    export DJANGO_DEFAULT_FROM_EMAIL={indigo@yourdomain.com}
    export DJANGO_EMAIL_HOST={smtp.yourdomain.com}
    export DJANGO_EMAIL_HOST_USER={indigo@yourdomain.com}
    export DJANGO_EMAIL_HOST_PASSWORD={email password}
    export DJANGO_EMAIL_PORT={Your SMTP Port number}
    export INDIGO_ORGANISATION='{Name of Your Organization}'
    export RECAPTCHA_PUBLIC_KEY={Your ReCaptcha Public Key}
    export RECAPTCHA_PRIVATE_KEY={Your ReCaptcha Private Key}
    export GOOGLE_ANALYTICS_ID={Your Google Analytics ID for the property}
    
   Now ensure that the ENV variables are in-use by refreshing the console session::
    
    # source ~/.bashrc

10. Now let us run the initial Indigo Deployment::

    # python manage.py migrate
    # python manage.py update_countries_plus
    # python manage.py loaddata languages_data.json.gz
    # python manage.py createsuperuser
    # python manage.py compilescss
    # python manage.py collectstatic --noinput -i docs -i \*scss 2>&1
    
   If everything worked out well, we should be able to test your installation in debug mode now::
    
    # python manage.py runserver 0.0.0.0:8000
    
   You should be able to connect to the host via your browser to http://ip-of-host:8000
    
   Press Ctrl+C to end the development server, we are now reasdy to deploy to production

11. Change DJANGO_DEBUG to false so that we can run a production server:

   Just like we did in step 9, we are just going to edit the ENV so that the debug flag is set to false::
    
    # nano ~/.bashrc
    
   Find the line you added earlier for export DJANGO_DEBUG=true and change it to read::
    
    export DJANGO_DEBUG=true
    
12. Create SSL Certificates:
 
   In Production Mode, Indigo requires an SSL connection, lets generate a key-pair inside of the indigo folder::
    
    # openssl req -new -x509 -days 365 -nodes -out server.crt -keyout server.key
    
13. Run Gunicorn webserver for production use::
 
    # gunicorn -k=gevent indigo.wsgi:application -t 600 --certfile=/root/indigo/server.crt --keyfile=/root/indigo/server.key -b=0.0.0.0:443 -w=4 --forwarded-allow-ips=* --proxy-allow-from=*
    
    You should now be able to connect to your Indigo instance at https://your-ip-address/

Background Tasks
----------------

Indigo can optionally do some operations in the background. It requires a worker or
cron job to run the ``django-background-tasks`` task queue. Indigo tasks are placed
in the ``indigo`` task queue. See `django-background-tasks <https://django-background-tasks.readthedocs.io/en/latest/>`
for more details on running background tasks.

To enable background tasks, set ``INDIGO.NOTIFICATION_EMAILS_BACKGROUND`` to True in ./indigo/settings.py
