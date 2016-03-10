.. _rest_public_guide:

Using the Public REST API
=========================

This guide is for developers who want to use the Indigo Public REST API
to fetch and render documents for users to read or download. We assume that
you have a basic understanding of web applications, REST APIs and the
`Akoma Ntoso <http://www.akomantoso.org/>`_ standard for legislation (acts).

See :ref:`rest_general_guide` for general API details such as content types and
what the fields of a Document are.

If you want to manage and edit a collection of legislation see :ref:`rest_app_guide` instead.

Public API
----------

The public API is a read-only API for exploring a collection of legislative documents. Using it, you can:

* get a list of all acts by country and year
* get the raw Akoma Ntoso XML of an act
* get an human-friendly HTML version of an act
* get an Atom feed of newly published acts

The public API relies heavily on FRBR URIs (and URI fragments) for identifying content, be sure to read up on FRBR URIs above.


.. note::

   When we use a URL such as ``/api/frbr-uri/`` in this guide, the ``frbr-uri`` part is a full FRBR URI, such as ``/za/act/1998/84/eng``.

Listing Acts
------------

.. code:: http

    GET /api/za/
    GET /api/za/act/
    GET /api/za/act/2007/
  
* Content types: JSON, PDF, EPUB

These endpoints list all acts for a country or year.  To list the available acts for a country you'll need the `two-letter country code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_ for the country.

Atom Feeds
----------

.. code:: http

    GET /api/za/summary.atom
    GET /api/za/full.atom
    GET /api/za/act/summary.atom
    GET /api/za/act/full.atom
    GET /api/za/act/2007/summary.atom
    GET /api/za/act/2007/full.atom

* Content types: Atom

There are two Atom feeds for documents: a summary feed (``summary.atom``) and a full content feed (``full.atom``). The summary feed has the act title, metadata and the act preface (if any) of each document. The full content feed has the full HTML content of each document.

The Atom feeds are paginated and contain the most recently updated documents first. The summary feeds contains more items per page than the full feeds because the latter are much larger. Follow the ``next`` links in the feeds to fetch additional pages.


Entire Act
----------

.. code:: http

    GET /api/frbr-uri

* Parameter ``coverpage``: should the response contain a generated coverpage? Use 1 for true, anything else for false. Default: 1. (HTML-only)
* Content types: JSON, XML, HTML, PDF, ePUB


This returns the entire contents of an act. For example, the English HTML version of ``/za/act/1998/84/eng`` is available at:

    ``http://indigo.code4sa.org/api/za/act/1998/eng.html``

The raw XML is available at:

    ``http://indigo.code4sa.org/api/za/act/1998/eng.xml``

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

* Content types: XML, HTML, PDF, ePUB

Using HTML Responses
--------------------

TODO:

* talk about CSS

