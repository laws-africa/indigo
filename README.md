Indigo
======

[![Build Status](https://travis-ci.org/OpenUpSA/indigo.svg)](http://travis-ci.org/OpenUpSA/indigo)

![Indigo logo](https://raw.githubusercontent.com/Code4SA/indigo/master/docs/logo.png "Indigo logo")

Indigo is AfricanLII's document management system for managing, capturing and publishing
legislation in the [Akoma Ntoso](http://www.akomantoso.org/) format.

It is a Django python web application using:

* [Django](http://djangoproject.com/)
* [Cobalt](http://cobalt.readthedocs.org/en/latest/) -- a lightweight Python library for working with Akoma Ntoso
* [Slaw](https://rubygems.org/gems/slaw) -- a Ruby Gem for generating Akoma Ntoso from PDFs and other documents
* [django-rest-framework](http://www.django-rest-framework.org/)
* [backbone.js](http://backbonejs.org/)
* [stickit.js](http://nytimes.github.io/backbone.stickit/)

Read the [full documentation at indigo.readthedocs.org](http://indigo.readthedocs.org/en/latest/index.html).

Local development
-----------------

Clone the repo:

```bash
git clone https://github.com/OpenUpSA/indigo.git
cd indigo
```

Ensure you have python 2.7, [virtualenv and pip](https://virtualenv.pypa.io/en/stable/installation/) installed.

Create and activate a virtualenv and install dependencies:

```bash
virtualenv env --no-site-packages
source env/bin/activate
pip install -r requirements.txt
```

Ensure you have [PostgreSQL](https://www.postgresql.org/) installed and running. Create a postgresql user with username and password `indigo`,
and create a corresponding database called `indigo`.

```bash
sudo su - postgres createuser -d -P indigo
sudo su - postgres createdb indigo
```

Then run migrations to setup the initial database:

```bash
python manage.py migrate
python manage.py update_countries_plus
```

If you have trouble connecting to your database, you may need to change the default database settings in `indigo/settings.py`:

    db_config = dj_database_url.config(default='postgres://indigo:indigo@localhost:5432/indigo')

Then create the superuser:

```bash
python manage.py createsuperuser
```

Finally, run the server:

```
python manage.py runserver
```

You'll need some ruby dependencies. We strongly recommend installing and using [RVM](http://rvm.io/)
or a similar Ruby version manager.

```bash
bundle install
```

To run the tests use:

```bash
python manage.py test
```

Production deployment
---------------------

Read the [documentation for details on deploying Indigo](http://indigo.readthedocs.org/en/latest/running/index.html).

License and Copyright
---------------------

The project is licensed under a [GNU GPL 3 license](LICENSE).

Indigo is Copyright 2015-2017 AfricanLII.
