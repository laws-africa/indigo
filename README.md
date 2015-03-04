Indigo
======

[![Build Status](https://travis-ci.org/Code4SA/indigo.svg)](http://travis-ci.org/Code4SA/indigo)

Indigo is AfricanLII's document management system for managing, capturing and publishing
legislation in the [Akoma Ntoso](http://www.akomantoso.org/) format.

It is a Django python web application using:

* [django](http://djangoproject.com/)
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

To support importing from PDF and other file formats, you'll need some ruby dependencies.

```bash
bundle install
```

We strongly recommend installing and using [RVM](http://rvm.io/) or a similar Ruby
version manager.

Production deployment
---------------------

Production deployment assumes you're running on heroku.

You will need

* a django secret key
* a New Relic license key

```bash
heroku create
heroku addons:add heroku-postgresql
heroku addons:add newrelic:stark
heroku config:set DJANGO_DEBUG=false \
                  DISABLE_COLLECTSTATIC=1 \
                  DJANGO_SECRET_KEY=some-secret-key \
                  NEW_RELIC_APP_NAME="Indigo" \
                  NEW_RELIC_LICENSE_KEY=some-license-key
git push heroku master
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

License
-------

The project is licensed under a [GNU GPL 3 license](LICENSE).
