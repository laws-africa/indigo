Indigo
======

Indigo is AfricanLII's document management system for managing, capturing and publishing
legislation in the Akoma Ntoso format.

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
                  DJANGO_SECRET_KEY=some-secret-key \
                  NEW_RELIC_APP_NAME="Indigo" \
                  NEW_RELIC_LICENSE_KEY=some-license-key
git push heroku master
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```
