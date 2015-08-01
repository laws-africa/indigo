Indigo
======

[![Build Status](https://travis-ci.org/Code4SA/indigo.svg)](http://travis-ci.org/Code4SA/indigo)

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

Clone the repo and ensure you have python, virtualenv and pip installed. 

```bash
virtualenv env --no-site-packages
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

To support importing from PDF and other file formats, you'll need some ruby
dependencies.  We strongly recommend installing and using [RVM](http://rvm.io/)
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

Production deployment assumes you're running on Heroku. We use [ddollar/heroku-buildpack-multi](https://github.com/ddollar/heroku-buildpack-multi)
because we need both Python and Ruby dependencies and a working JVM.

* Python is needed for the core application
* Ruby and Java are needed for the Slaw library to parse PDFs into XML

You will need:

* a django secret key
* a New Relic license key
* AWS credentials for S3 uploads

```bash
heroku create
heroku addons:add heroku-postgresql
heroku addons:add newrelic:stark
heroku config:set BUILDPACK_URL=https://github.com/ddollar/heroku-buildpack-multi.git \
                  DJANGO_DEBUG=false \
                  DISABLE_COLLECTSTATIC=1 \
                  DJANGO_SECRET_KEY=some-secret-key \
                  NEW_RELIC_APP_NAME="Indigo" \
                  NEW_RELIC_LICENSE_KEY=some-license-key \
                  AWS_ACCESS_KEY_ID=aws-access-key \
                  AWS_SECRET_ACCESS_KEY=aws-secret-key
git push heroku master
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

License
-------

The project is licensed under a [GNU GPL 3 license](LICENSE).
