# Indigo

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/495add45b788408284b48c0e045ca408)](https://app.codacy.com/app/longhotsummer/indigo?utm_source=github.com&utm_medium=referral&utm_content=laws-africa/indigo&utm_campaign=Badge_Grade_Dashboard)
[![Build Status](https://travis-ci.org/laws-africa/indigo.svg)](http://travis-ci.org/laws-africa/indigo) [![Coverage Status](https://coveralls.io/repos/github/laws-africa/indigo/badge.svg?branch=master)](https://coveralls.io/github/laws-africa/indigo?branch=master)

![Indigo logo](https://raw.githubusercontent.com/Code4SA/indigo/master/docs/logo.png "Indigo logo")

Indigo is AfricanLII's document management system for managing, capturing and publishing
legislation in the [Akoma Ntoso](http://www.akomantoso.org/) format.

It is a Django python web application using:

* [Django 2](http://djangoproject.com/)
* [Cobalt](http://cobalt.readthedocs.io/en/latest/) -- a lightweight Python library for working with Akoma Ntoso
* [Slaw](https://rubygems.org/gems/slaw) -- a Ruby Gem for generating Akoma Ntoso from PDFs and other documents
* [django-rest-framework](http://www.django-rest-framework.org/)
* [backbone.js](http://backbonejs.org/)
* [stickit.js](http://nytimes.github.io/backbone.stickit/)

Read the [full documentation at indigo.readthedocs.io](http://indigo.readthedocs.io/en/latest/index.html).

## Local development

Clone the repo:

```bash
git clone https://github.com/laws-africa/indigo.git
cd indigo
```

Ensure you have python 3.6, [virtualenv and pip](https://virtualenv.pypa.io/en/stable/installation/) installed.

Create and activate a virtualenv and install dependencies:

```bash
virtualenv env -p python3.6
source env/bin/activate
pip install -e '.[test]'
```

Ensure you have [PostgreSQL](https://www.postgresql.org/) installed and running. Create a postgresql user with username and password `indigo`,
and create a corresponding database called `indigo`.

```bash
sudo su - postgres -c 'createuser -d -P indigo'
sudo su - postgres -c 'createdb indigo'
```

Check that you can connect to the postgresql database as your regular shell user (not indigo user) by means of password authentication:

```
psql -h localhost indigo indigo
```

If you can't connect, you can modify your `pg_hba.conf` (`/etc/postgresql/9.6/main/pg_hba.conf` for postgresql 9.6) to allow md5 encrypted password authentication for users on localhost by adding a line like this:

```
local	all		all     md5
```

Then run migrations to setup the initial database:

```bash
python manage.py migrate
python manage.py update_countries_plus
python manage.py loaddata languages_data.json.gz
```

If you have trouble connecting to your database, you may need to change the default database settings in `indigo/settings.py`:

    db_config = dj_database_url.config(default='postgres://indigo:indigo@localhost:5432/indigo')

Then create the superuser:

```bash
python manage.py createsuperuser
```

Now, run the server:

```
python manage.py runserver
```

Now login at [http://localhost:8000](http://localhost:8000) and create a country by going to [http://localhost:8000/admin](http://localhost:8000/admin), choosing *Countries* under *Indigo API* and clicking *Add Country*.

Now give yourself all the permissions to work in that country by clicking on your name in the top right corner and choosing Profile. In the Badges Earned section, award yourself all the badges in the dropdown list.

### Ruby and other non-Python dependencies

You won't be able to import documents yet. First, you'll need to install Ruby and the Slaw parser library.
We strongly recommend installing and using [RVM](http://rvm.io/) or a similar Ruby version manager. You'll
need Ruby version 2.3.

Once you've install Ruby, install [Bundler](https://bundler.io/) and the Indigo dependencies:

```bash
gem install bundler
bundle install
```

You can test that Slaw is installed with `slaw --version`:

```bash
$ slaw --version
slaw 1.0.0
```

You will also need `pdftotext` to import PDF files. On Mac, you can use Homebrew and run `brew install poppler`.


## Adding translation strings

Each indigo package has its own translations in the `locale` directory. Translations for strings are added on [CrowdIn](https://crowdin.com/project/lawsafrica-indigo).

If you have added or changed strings that need translating, you must [tell Django to update the .po files](https://docs.djangoproject.com/en/2.2/topics/i18n/translation/#localization-how-to-create-language-files) so that translations can be supplied through CrowdIn.

```bash
for app in indigo indigo_api indigo_za; do pushd $app; django-admin makemessages -a; popd; done
```

And then commit the changes. CrowdIn will pick up any changed strings and make them available for translation. Once they are translated, it will
open a pull request to merge the changes into master.

Once merged into master, you must [tell Django to compile the .po files to .mo files](https://docs.djangoproject.com/en/2.2/topics/i18n/translation/#compiling-message-files):

```bash
django-admin compilemessages --settings indigo.settings
```

And then commit the changes.


## npm module dependencies

Indigo uses a small number of node modules written in ES6. They need to be compiled into a single JS file
because Indigo doesn't use ES6.

To do this, install [browserify](http://browserify.org/), then:

```
npm install
browserify indigo_app/static/lib/dom-utils.src.js > indigo_app/static/lib/dom-utils.js
```


## Testing

To run the tests use:

```bash
python manage.py test
```

## Production deployment

Read the [documentation for details on deploying Indigo](http://indigo.readthedocs.org/en/latest/running/index.html).

## Releasing a New Version

1. Run the tests!
2. Update VERSION appropriately
3. Update `docs/changelog.rst`
4. Commit changes
5. Tag: `git tag vX.X.X` and push to github `git push; git push --tags`

## License and Copyright

The project is licensed under a [GNU GPL 3 license](LICENSE).

Indigo is Copyright 2015-2020 AfricanLII.
