.. _rest_general_guide:

General API Guidelines
======================

This guide is for developers who want to use either the
Indigo Public REST API or the Indigo Application REST API.
We assume that you have a basic understanding of web applications, REST APIs
and the `Akoma Ntoso <http://www.akomantoso.org/>`_ standard for legislation
(acts).

This guide covers details that are shared by both APIs. For more information
on each API, see :ref:`rest_app_guide` and :ref:`rest_public_guide`.

Location of the API
-------------------

The API is available at http://indigo.code4sa.org/api/.

It is easy to explore using a browser and follows normal REST semantics using
HTTP methods such as ``GET``, ``POST``, ``PUT`` and ``DELETE``.

Content types
-------------

Some REST calls can return content in multiple formats. You can specify the
content type of a response by placing ``.format`` at the end of the URL
or including an ``Accept:`` header in the request. In most cases the default
response type is JSON.

* ``.json`` or ``Accept: application/json``: return JSON
* ``.xml`` or ``Accept: application/xml``: return Akoma Ntoso XML
* ``.html`` or ``Accept: text/html``: return human friendly HTML

.. note::

   Not all responses support all formats, the documentation will be explicit
   about what is supported.

When submitting data to the API in a PUT or POST request, encode it either
as JSON or using form encoding and include the appropriate ``Content-Type`` header.

An example POST request with JSON encoded values:

.. code-block:: HTTP

    POST /api HTTP/1.1
    Accept: application/json
    Content-Type: application/json; charset=utf-8
    
    {
        "key": "value"
    }

An example POST request with form encoded values:

.. code-block:: HTTP

    POST /auth/login/ HTTP/1.1
    Accept: application/json
    Content-Type: application/x-www-form-urlencoded; charset=utf-8
   
    key=value

All our examples will use the JSON format for requests.

.. seealso::

   For more information on content type negotation see http://www.django-rest-framework.org/api-guide/content-negotiation/

Document (Act) Details
----------------------

Both APIs describe a document (an act) as a JSON object, such as:

.. code-block:: json

    {
      "amended_versions": [{
        "id": 2,
        "expression_date": "2005-03-01"
      }],
      "amendments": [{
        "date": "2005-03-01",
        "amending_title": "Act to Amend Act 10 of 2004",
        "amending_uri": "/za/act/2005/1",
        "amending_id": null
      }],
      "assent_date": "2004-03-03",
      "content_url": "http://indigo.code4sa.org/api/documents/1/content",
      "country": "za",
      "created_at": "2015-01-14T15:57:08.497844Z",
      "draft": false,
      "frbr_uri": "/za/act/2004/10/eng",
      "expression_date": "2004-05-21",
      "commencement_date": "2004-05-21",
      "id": 1,
      "language": "eng",
      "locality": null,
      "nature": "act",
      "number": "10",
      "publication_date": "2004-05-21",
      "publication_name": "Government Gazette",
      "publication_number": "179",
      "published_url": "http://indigo.code4sa.org/api/za/act/2004/10/",
      "stub": false,
      "subtype": null,
      "tags": ["checks needed"],
      "title": "Act 10 of 2004",
      "updated_at": "2015-02-17T12:23:48.394662Z",
      "url": "http://indigo.code4sa.org/api/documents/1.json",
      "year": "2004"
    }

Each of these fields is described in the table below.

================= =================================================================================== ========== =========================
Field             Description                                                                         Type       Default for new documents
================= =================================================================================== ========== =========================
amendments        List of amendments that have been applied to create this version of the document.   See below  ``[]``
amended_versions  List of different amended versions of this document in the library. Read-only.      See below  ``[]``
assent_date       Date when the document was assented to. Optional.                                   ISO8601
content_url       URL of the full content of the document. Read-only.                                 URL        Auto-generated
country           ISO 3166-1 alpha-2 country code that this document is applicable to.                String
created_at        Timestamp of when the document was first created. Read-only.                        ISO8601    Current time
draft             Is this a draft document or is it available in the public API?                      Boolean    ``true``
expression_date   Date of this expression (or publication). Required.                                 ISO8601    Publication date
commencement_date Date of this commencement of most of the document. Optional.                        ISO8601
frbr_uri          FRBR URI for this document.                                                         String     None, a value must be provided
id                Unique ID of this document. Read-only.                                              Integer    Auto-generated
language          Three letter ISO-639-2 language code for the language of the document.              String     ``"eng"``
locality          The code of the locality within the country. Optional. Read-only.                   String
nature            The nature of this document, normally "act".                                        String     ``"act"``
number            Number of this act in its year of publication, or some other unique way of          String
                  identifying it within the year
published_url     URL of where the published document is available.                                   URL        Auto-generated
                  This will be null if draft is true
stub              Is this a stub document? Stub documents are generally empty.                        Boolean    ``false``
subtype           Subtype code of the document. Optional. Read-only.                                  String
tags              List of string tags linked to the document. Optional.                               Strings    ``[]``
title             Document short title.                                                               String     ``"(untitled)"``
updated_at        Timestamp of when the document was last updated. Read-only.                         ISO8601    Current time
url               URL for fetching details of this document. Read-only.                               URL        Auto-generated
year              Year of publication                                                                 String 
================= =================================================================================== ========== =========================

In some cases, a document may also contain a ``content`` field.

============== =================================================================================== ========== =========================
Field          Description                                                                         Type       Default for new documents
============== =================================================================================== ========== =========================
content        Raw XML content of the entire document.                                             String     Basic document content
============== =================================================================================== ========== =========================

Amendments
----------

Amendments describe documents that made amendments to this document. The amending document doesn't need to be stored
in the system, but it does need a date, title and a URI. If it **is** in the system, then ``amending_id``
will be its document id, otherwise it will be ``null``.

=============== =================================================================================== ==========
Field           Description                                                                         Type
=============== =================================================================================== ==========
amending_id     Document id of the amending document, if in the library. Read-only.                 Integer
amending_title  Title of the amending document.                                                     String
amending_uri    FRBR URI of the amending document.                                                  String
date            Date of the amending document, the date at which the amendment took place.          ISO8601
=============== =================================================================================== ==========

Amended Versions
----------------

The amended versions are those documents in the library with the same FRBR URI and different expression dates. They are looked up
automatically for a document, so it is important that the FRBR URI and expression date are correct for all documents.
All fields are read-only.

=============== =================================================================================== ==========
Field           Description                                                                         Type
=============== =================================================================================== ==========
id              Document id in the library.                                                         Integer
expression_date Date of the expression (or publication) of the document.                            ISO8601
=============== =================================================================================== ==========


Next Steps
----------

Now you're ready to read the guides for the two APIs:

* :ref:`rest_app_guide`
* :ref:`rest_public_guide`

