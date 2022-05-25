# Indigo

![Build status](https://github.com/laws-africa/indigo/workflows/Test/badge.svg) [![Coverage Status](https://coveralls.io/repos/github/laws-africa/indigo/badge.svg?branch=master)](https://coveralls.io/github/laws-africa/indigo?branch=master)

![Indigo logo](https://raw.githubusercontent.com/Code4SA/indigo/master/docs/logo.png "Indigo logo")

Indigo is Laws.Africa's legislation database for managing, consolidating and publishing
legislation in the [Akoma Ntoso](http://www.akomantoso.org/) format.

It is a Django python web application using:

* [Django](http://djangoproject.com/)
* [Cobalt](http://cobalt.readthedocs.io/en/latest/) -- a lightweight Python library for working with Akoma Ntoso
* [Slaw](https://rubygems.org/gems/slaw) -- a Ruby Gem for generating Akoma Ntoso from PDFs and other documents
* [django-rest-framework](http://www.django-rest-framework.org/)

Read the [full documentation at indigo.readthedocs.io](http://indigo.readthedocs.io/en/latest/index.html).

## Local development
Refer to https://indigo.readthedocs.io/en/latest/running/index.html

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
python manage.py compilemessages
```

And then commit the changes.


## npm module dependencies

Indigo is migrating to modules written in ES6 using Vue. This code needs to be compiled into a single JS file using webpack.

```
npm install
npx webpack
```

During development, using `npx webpack -w` to watch for changes and recompile automatically.

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
