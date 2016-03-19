# Indigo Web

Stylesheets for use with HTML documents published using the [Indigo platform](https://indigo.readthedocs.org).
They make Akoma Ntoso documents look beautiful.

## Usage

Install indigo-web using bower:

    $ bower install indigo-web

Then use either the compiled CSS:

    <link rel="stylesheet" type="text/css" href="indigo-web/css/akoma-ntoso.min.css">

Or use the SCSS files:

    @import 'indigo-web/scss/akoma-ntoso';

## Overriding variables

You can override variables when using SCSS by copying them from ``_variables.scss`` into ``_custom.scss`` and changing
their values.

# Version history

## 0.1.1 (19 March 2015)

* Bump base font size to 15px to improve legibility with serif fonts.

## 0.1.0 (19 March 2015)

* Initial release

# Releasing a new version

1. Compile the SCSS:

```bash
scss -t compressed scss/akoma-ntoso.scss css/akoma-ntoso.min.css
scss scss/akoma-ntoso.scss css/akoma-ntoso.css
git add css/*
```

2. Update the README.md to describe changes.
3. Create and tag a release on GitHub

# License

Licensed under an MIT license.
