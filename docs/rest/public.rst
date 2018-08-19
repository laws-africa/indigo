.. _rest_public_guide:

Using the Indigo API
====================

This guide is for developers who want to use the API to fetch legislative works. We assume that you have a basic understanding of REST APIs and the `Akoma Ntoso <http://www.akomantoso.org/>`_ standard for legislation (acts in particular).

.. note:: 

   The API relies heavily on Akoma Ntoso FRBR URIs, which are described in the `Akoma Ntoso naming convention standard <http://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html>`_.

Getting Started
---------------

The API is a read-only API for listing and fetching published versions of legislative works. Using it, you can:

* get a list of all works by country and year
* get a JSON description of a work
* get Akoma Ntoso XML for a work
* get a human-friendly HTML version of a work

.. note::

   When we use a URL such as ``/api/frbr-uri/`` in this guide, the ``frbr-uri`` part is a full FRBR URI, such as ``/za/act/1998/84/eng``.

Location of the API
-------------------

The API is available at the `/api/` URL of your Indigo installation.

Authentication
--------------

You must authenticate all calls to the API by including your API authentication token in your request. Include in your request an HTTP header called ``Authorization`` with a value of ``Token <your-api-token>``. For example::

    Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

.. _pagination:

Pagination
----------

API calls that return lists will be paginated and return a limited number
of items per page. The response includes information on the total number of items and the URLs to use to fetch the next and previous pages of items.

Here's an example of the first page of a paginated response with 250 total items and two pages:

.. code-block:: json

    {
      "count": 250,
      "next": "https://indigo.example.com/api/za.json?page=2",
      "previous": null,
      "results": [ "..." ]
    }

In this case, fetching the ``next`` URL will return the second (and final) page.

Content types
-------------

Some API calls can return content in multiple formats. You can specify the
required content of your request by placing ``.format`` at the end of the URL.
In most cases the default response type is JSON.

* ``.json`` or ``Accept: application/json``: return JSON
* ``.xml`` or ``Accept: application/xml``: return Akoma Ntoso XML
* ``.html`` or ``Accept: text/html``: return human friendly HTML
* ``.epub`` or ``Accept: application/epub+zip``: return an ePUB (ebook) document
* ``.pdf`` or ``Accept: application/pdf``: return a PDF document
* ``.zip`` or ``Accept: application/zip``: return a ZIP file with the document XML and media attachments

.. note::

   Not all responses support all formats, the documentation will be explicit
   about what is supported.

Fetching a Work
---------------

.. code:: http

    GET /api/frbr-uri.json

This returns the detail of a work as a JSON document. For example, this is the
description of the English version of Act 55 of 1998.

.. code-block:: json

    {
      "url": "https://indigo.example.com/api/za/act/1998/55/eng.json",
      "title": "Employment Equity Act, 1998",
      "created_at": "2017-12-23T10:05:55.105543Z",
      "updated_at": "2018-06-07T08:07:51.170250Z",
      "country": "za",
      "locality": null,
      "nature": "act",
      "subtype": null,
      "year": "1998",
      "number": "55",
      "frbr_uri": "/act/1998/55",
      "expression_frbr_uri": "/act/1998/55/eng@2005-10-03",
      "publication_date": "1998-10-19",
      "publication_name": "Government Gazette",
      "publication_number": "19370",
      "expression_date": "2014-01-17",
      "commencement_date": "1999-05-14",
      "assent_date": "1998-10-12",
      "language": "eng",
      "stub": false,
      "repeal": null,
      "amendments": [
        {
          "date": "2014-01-17",
          "amending_title": "Employment Equity Amendment Act, 2013",
          "amending_uri": "/za/act/2013/47"
        },
      ],
      "points_in_time": [
        {
          "date": "2014-01-17",
          "expressions": [
            {
              "url": "https://indigo.example.com/api/act/1998/55/eng@2014-01-17",
              "language": "eng",
              "expression_frbr_uri": "/act/1998/55/eng@2014-01-17",
              "expression_date": "2014-01-17",
              "title": "Employment Equity Act, 1998"
            }
          ]
        }
      ],
      "links": [
        {
          "href": "https://indigo.openbylaws.org.za/api/za-wc033/act/by-law/2005/beaches/eng.html",
          "title": "HTML",
          "rel": "alternate",
          "mediaType": "text/html"
        },
        { "..." }
      ]
    }

The fields of the response are described in the table below.

=================== =================================================================================== ==========
Field               Description                                                                         Type
=================== =================================================================================== ==========
amendments          List of amendments that have been applied to create this expression of the work.    See below
assent_date         Date when the work was assented to.                                                 ISO8601
content_url         URL of the full content of the work.                                                URL
country             ISO 3166-1 alpha-2 country code that this work is applicable to.                    String
created_at          Timestamp of when the work was first created.                                       ISO8601
draft               Is this a draft work or is it available in the public API?                          Boolean
expression_date     Date of this expression of the work.                                                ISO8601
commencement_date   Date on which this work commences.                                                  ISO8601
expression_frbr_uri FRBR URI of this expression of this work.                                           String
frbr_uri            FRBR URI for this work.                                                             String
id                  Unique ID of this work.                                                             Integer
language            Three letter ISO-639-2 language code for this expression of the work.               String
links               A description of links to other formats of this expression that are available
                    through the API.
locality            The code of the locality within the country.                                        String
nature              The nature of this work, normally "act".                                            String
number              Number of this work with its year, or some other unique way of identifying it       String
                    within the year.
publication_date    Date of original publication of the work.                                           ISO8601
publication_name    Name of the publication in which the work was originally published.                 String
publication_number  Number of the publication in which the work was originally published.               String
repeal              Description of the repeal of this work, if it has been repealed.                    See below
stub                Is this a stub work? Stub documents are generally empty.                            Boolean
subtype             Subtype code of the work.                                                           String
tags                List of string tags linked to the work. Optional.                                   Strings
title               Short title of the work, in the appropriate language.                               String
updated_at          Timestamp of when the work was last updated.                                        ISO8601
url                 URL for fetching details of this work.                                              URL
year                Year of the work.                                                                   String
=================== =================================================================================== ==========


Fetching the Akoma Ntoso of a Work
..................................

.. code:: http

    GET /api/frbr-uri.xml

This returns the Akoma Ntoso XML of a work.

For example, fetch the English Akoma Ntoso version of ``/za/act/1998/84`` by calling:

.. code:: http

    GET /api/za/act/1998/84/eng.xml

Fetching a Work as HTML
.......................

.. code:: http

    GET /api/frbr-uri.html

Fetch the HTML version of a work by specify `.html` as the format extensions in the URL.

* Parameter ``coverpage``: should the response contain a generated coverpage? Use 1 for true, anything else for false. Default: 1.
* Parameter ``standalone``: should the response by a full HTML document, including CSS, that can stand on its own? Use 1 for true, anything else for false. Default: false.
* Parameter ``resolver``: the fully-qualified URL to use when resolving absolute references to other Akoma Ntoso documents. Use 'no' or 'none' to disable. Default is to use the Indigo resolver.
* Parameter ``media-url``: the fully-qualified URL prefix to use when generating links to media, such as images.

For example, fetch the English HTML version of ``/za/act/1998/84`` by calling:

.. code:: http

    GET /api/za/act/1998/84/eng.html

Listing Works
-------------

.. code:: http

    GET /api/za/
    GET /api/za/act/
    GET /api/za/act/2007/
  
* Content types: JSON, PDF, EPUB, ZIP

These endpoints list all works for a country or year.  To list the available works for a country you'll need the `two-letter country code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_ for the country.

Acts at a Point in Time
-----------------------

A URI such as ``/za/act/1998/84/eng`` actually refers to the latest (current) version of the act.

An act may be amended multiple times over its lifetime. You can retrieve the version of an act as it appeared after a dated amendment, if available, by specifyng the date in the URI in the format ``@YYYY-MM-dd``. For example, ``/za/act/1998/84/eng@2012-01-01`` is the version of Act 84 of 1998 after the amendment on date 2012-01-01 has been applied. If there was no amendment of that document on that exact date, a 404 will be returned.

You can fetch the very first version of the act by using a ``@`` without a date: ``/za/act/1998/84/eng@``.

If you don't know on which exact dates amendments were made, you can get the version of the act as it would have looked on a particular date (if available) by placing ``:YYYY-MM-DD`` at the end of the URI, for example: ``/za/act/1998/84/eng:2012-06-01``. Indigo will find the most recent amended version at or before that date.

Components and formats are placed after the date portion, such as ``/za/act/1998/84/eng@2012-01-01.json``.

Table of Contents
-----------------

.. code:: http

    GET /api/frbr-uri/toc.json

* Content types: JSON

Get a description of the table of contents (TOC) of an act. This includes the chapters, parts, sections and schedules that make
up the act, based on the structure captured by the Indigo editor.

Each item in the table of contents has this structure:

.. code-block:: json

    {
      "id": "chapter-1",
      "type": "chapter",
      "num": "1",
      "heading": "Interpretation",
      "title": "Chapter 1 - Interpretation",
      "component": "main",
      "subcomponent": "chapter/1",
      "url": "http://indigo.code4sa.org/api/za/act/1998/10/eng/main/chapter/1",
      "children": [ "..." ]
    }

Each of these fields is described in the table below.

================= =================================================================================== ==========
Field             Description                                                                         Type
================= =================================================================================== ==========
id                The unique XML element id of this item. (optional)                                  String
type              The Akoma Ntoso element name of this item.                                          String
num               The number of this item, such as a chapter, part or section number. (optional)      String
heading           The heading of this item (optional)                                                 String
title             A derived, friendly title of this item, taking ``num`` and ``heading`` into         String
                  account and providing good defaults if either of those is missing.
component         The component of the Akoma Ntoso document that this item is a part of, such as      String
                  ``main`` for the main document, or ``schedule1`` for the first schedule.
subcomponent      The subcomponent of the component that this item is a part of, such as a chapter.   String
                  (optional)
url               The API URL for this item, which can be used to fetch XML, HTML and other details   String
                  of just this part of the document.
children          A possibly-empty array of TOC items that are children of this item.                 Array
================= =================================================================================== ==========

Fetching Parts, Chapters and Sections
-------------------------------------

You can use the ``url`` field from an item in the table of contents to fetch the details of just that item
in various forms.

.. code:: http

    GET /api/frbr-uri/toc-item-uri.format

* Content types: XML, HTML, PDF, ePUB, ZIP

Using HTML Responses
--------------------

Indigo transforms Akoma Ntoso XML into HTML5 content that looks best when styled with
`Indigo Web <https://github.com/Code4SA/indigo-web>`_ stylesheets. You can link
to the stylesheets provided by that package, or you can pull them into your website.

Search
------

.. code:: http

    GET /api/search/works?q=<search-term>

* Parameter ``q``: the search string
* Filter parameters:

  * ``country``
  * ``draft``
  * ``frbr_uri``, ``frbr_uri__startswith``
  * ``language``
  * ``stub``
  * ``expression_date``, ``expression_date__lte``, ``expression_date__gte``

* Content types: JSON

This API searches through works (acts). It returns all works that match the
search term, in search rank order. Each result also has a numeric ``_rank`` and
an HTML ``_snippet`` with highlighted results.

Use additional parameters to filter the search results.

If more than one expression of a particular work matches the search, then only
the most recent matching expression is returned. If you would like all
matching documents, use the ``/api/search/documents`` search API.
