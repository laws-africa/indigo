# Indigo Web

[![Build Status](https://travis-ci.org/Code4SA/indigo-web.svg)](http://travis-ci.org/Code4SA/indigo-web)

Stylesheets for use with HTML documents published using the [Indigo platform](https://indigo.readthedocs.org).
They make Akoma Ntoso documents look beautiful.

## Usage

### From CDN

Use the assets directly from a CDN:

    <link rel="stylesheet" type="text/css" href="//indigo-web.openup.org.za/dist/0.1.3/css/akoma-ntoso.min.css">

### From your server

Install indigo-web using bower:

    $ bower install indigo-web

Then use either the compiled CSS:

    <link rel="stylesheet" type="text/css" href="indigo-web/css/akoma-ntoso.min.css">

Or use the SCSS files:

    @import 'indigo-web/scss/akoma-ntoso';

## Overriding variables

You can override variables when using SCSS by copying them from ``_variables.scss`` into ``_custom.scss`` and changing
their values.

## Building

To build changes:

* gem install sass
* ./build.sh
* git add css/*

## Release process

* update VERSION
* update Version History (below)
* push to github and tag release
* Travis should build the tagged version and release it

# Version history

## 0.1.3 (22 October 2017)

* Styling for images

## 0.1.2 (19 March 2017)

* Styling for rendering commencement and assent notices as list items, not headings.

## 0.1.1 (19 March 2016)

* Bump base font size to 15px to improve legibility with serif fonts.

## 0.1.0 (19 March 2016)

* Initial release

# License

Licensed under an MIT license.
