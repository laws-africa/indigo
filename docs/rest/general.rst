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

Some REST responses can in multiple formats. You can choose the content type of
a response by including an ``Accept:`` header in the request or by placing
``.format`` at the end of the URL. In most cases the default response
type is JSON.

* ``.json`` or ``Accept: application/json``: return JSON
* ``.xml`` or ``Accept: application/xml``: return Akoma Ntoso XML
* ``.html`` or ``Accept: text/html``: return human friendly HTML

To explicitly request a JSON response include ``Accept: application/json``
in the request, or put ``.json`` at the end of the URL. To request XML,
using ``Accept: application/xml`` or put ``.xml`` at the end of the URL.

.. note::

   Not all responses support all formats, the documentation will be explicit
   about what is supported.

When submitting data to the API in a PUT or POST request, encode it either
as JSON or as form encoding, including the appropriate ``Content-Type`` header.

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
      "id": 1,
      "url": "http://indigo.code4sa.org/api/documents/1.json",
      "frbr_uri": "/za/act/2004/10/eng",
      "draft": false,
      "created_at": "2015-01-14T15:57:08.497844Z",
      "updated_at": "2015-02-17T12:23:48.394662Z",
      "title": "Sample Act 10 of 2004",
      "country": "za",
      "number": "10",
      "year": "2004",
      "nature": "act",
      "publication_date": "2004-05-21",
      "publication_name": "Government Gazette",
      "publication_number": "179",
      "content_url": "http://indigo.code4sa.org/api/documents/1/content",
      "published_url": "http://indigo.code4sa.org/api/za/act/2004/10/"
    }

Each of these fields is described in the table below.

============== =================================================================================== ========== =========================
Field          Description                                                                         Type       Default for new documents
============== =================================================================================== ========== =========================
id             Unique ID of this document. Read-only.                                              Integer    Auto-generated
url            URL for fetching details of this document. Read-only.                               URL        Auto-generated
frbr_uri       FRBR URI for this document.                                                         String     None, a value must be provided
draft          Is this a draft document or is it available in the public API?                      Boolean    ``true``
created_at     Timestamp of when the document was first created. Read-only.                        ISO8601    Current time
updated_at     Timestamp of when the document was last updated. Read-only.                         ISO8601    Current time
title          Document short title.                                                               String     ``"(untitled)"``
country        ISO 3166-1 alpha-2 country code that this document is applicable to.                String
number         Number of this act in its year of publication, or some other unique way of          String
               identifying it within the year
year           Year of publication                                                                 String 
nature         The nature of this document, normally "act".                                        String     ``"act"``
content_url    URL of the full content of the document. Read-only.                                 URL        Auto-generated
published_url  URL of where the published document is available.                                   URL        Auto-generated
               This will be null if draft is true
============== =================================================================================== ========== =========================

In some cases, a document may also contain ``content`` fields.

============== =================================================================================== ========== =========================
Field          Description                                                                         Type       Default for new documents
============== =================================================================================== ========== =========================
content        Raw XML content of the entire document.                                             String     Basic document content
============== =================================================================================== ========== =========================


Next Steps
----------

Now you're reading to read the guides for the two APIs:

* :ref:`rest_app_guide`
* :ref:`rest_public_guide`

