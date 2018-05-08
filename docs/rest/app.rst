.. _rest_app_guide:

Using the Application REST API
==============================

This guide is for developers who want to use the Indigo REST Application API to
manage and edit works and documents. We assume that you have a basic understanding of web
applications, REST APIs and the `Akoma Ntoso <http://www.akomantoso.org/>`_
standard for legislation (acts).

See :ref:`rest_general_guide` for general API details such as content types and
what the fields of a Document are.

If you only want to fetch and render published legislation and don't care
about works or editing legislation, see :ref:`rest_public_guide` instead.

Application API
---------------

The application API is the REST API used by the web editor to manage documents. With it you can:

* create, edit, update and delete works
* list works
* create, edit, update and delete documents
* list and search for documents
* manage users and passwords

The API is available at http://indigo.code4sa.org/api/.

It is easy to explore using a browser and follows normal REST semantics using
HTTP methods such as ``GET``, ``POST``, ``PUT`` and ``DELETE``.

Authentication
--------------

Write operations (POST, PUT and DELETE) require authentication with a token. To get an authentication token,
use

* ``POST /auth/login/``

  * ``username``: your email address 
  * ``password``: your password

and store the returned ``key`` as your token.

.. code-block:: HTTP

    POST /auth/login/ HTTP/1.1
    Accept: application/json
    Accept-Encoding: gzip, deflate
    Content-Length: 56
    Content-Type: application/json; charset=utf-8

    {
        "password": "password",
        "username": "me@example.com",
    }

.. code-block:: HTTP

    HTTP/1.0 200 OK
    Allow: POST, OPTIONS
    Connection: close
    Content-Type: application/json

    {
        "key": "118365019bd8a541e9211dc12741c927225ec00a"
    }

In subsequent requests that require authentication, include the token as a header ``Authorization: Token 118365019bd8a541e9211dc12741c927225ec00a``.

.. seealso::

   For more information on token authentication, see the `authentication documentation for the Django Rest Framework <http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication>`_.

Works
-----

A Work is an Act, a by-law, a regulation, and so on. In Indigo, a work doesn't
have any content -- it's just a description of the basic details of the act (or
by-law, etc.). A work can be associated with many documents, each of which is an
*expression* of the work.

An Indigo work is uniquely identified by its FRBR URI. Documents are linked to a work through
a common FRBR URI.

Documents inherit a number of fields from a work, such as the FRBR URI, publication date, repeal status, etc.

List Works
..........

.. code:: http

    GET /api/works

Lists the works. The results will be :ref:`paginated <pagination>`.

Get a Work
..........

.. code:: http

    GET /api/works/{id}

Fetches a JSON description of a work. For example:

.. code-block:: json

    {
      "assent_date": null,
      "commencement_date": "2018-04-11",
      "country": "za",
      "created_at": "2018-04-07T11:59:28.181610Z",
      "created_by_user": {
        "id": 1,
        "display_name": "Greg K."
      },
      "frbr_uri": "/za/act/2018/2",
      "id": 246,
      "locality": null,
      "nature": "act",
      "number": "2",
      "publication_date": "2018-04-11",
      "publication_name": "Government Gazette",
      "publication_number": 1234,
      "repealed_by": null,
      "repealed_date": null,
      "subtype": null,
      "title": "An Act",
      "updated_at": "2018-04-07T11:59:28.181651Z",
      "updated_by_user": {
        "id": 1,
        "display_name": "Greg K."
      },
      "url": "http://indigo.code4sa.org/api/works/246",
      "year": "2018"
    }

Each of these fields is described in the table below.

================= =================================================================================== ========== =========================
Field             Description                                                                         Type       Default for new works
================= =================================================================================== ========== =========================
assent_date       Date when the work was assented to. Optional.                                       ISO8601
commencement_date Date of this commencement of most of the work. Optional.                            ISO8601
commencing_work   Work that determined the commencement date, if any. Optional.                       Object
country           ISO 3166-1 alpha-2 country code that this work is applicable to.                    String
created_at        Timestamp of when the work was first created. Read-only.                            ISO8601    Current time
frbr_uri          FRBR URI for this work.                                                             String     None, a value must be provided
id                Unique ID of this work. Read-only.                                                  Integer    None, a value must be provided
locality          The code of the locality within the country. Optional. Read-only.                   String
nature            The nature of this work, normally "act".                                            String     ``"act"``
number            Number of this act in its year of publication, or some other unique way of          String
                  identifying it within the year
repealed_by       Work that repealed this work, if any. Optional.                                     Object
repealed_date     Date when this work was repealed. Optional.                                         ISO8601
subtype           Subtype code of the work. Optional. Read-only.                                      String
title             work short title.                                                                   String     None, a value must be provided
updated_at        Timestamp of when the work was last updated. Read-only.                             ISO8601    Current time
url               URL for fetching details of this work. Read-only.                                   URL        Auto-generated
year              Year of publication                                                                 String 
================= =================================================================================== ========== =========================

Update a Work
.................

.. code:: http

    PUT /api/work/{id}
    PATCH /api/work/{id}

* Parameters:

  * all the work fields described above.

Updates a work. Use `PUT` when updating all the details of a work. Use `PATCH` when updating only some fields.

Delete a Work
.................

.. code:: http

    DELETE /api/works/{id}

Marks the work as deleted. The document can be recovered from the Django Admin area, but will never show up in any API
otherwise.

Works with linked documents cannot be deleted.

Create a Work
.............

.. code:: http

    POST /api/works

* Parameters:

  * all the document fields described above.

Documents
---------

List Documents
..............

.. code:: http

    GET /api/documents

Lists the documents in the library. The results will be :ref:`paginated <pagination>`.

Get a Document
..............

.. code:: http

    GET /api/documents/{id}

Fetches a JSON description of a document. This does not include the full content or body of the document since those may be very large.

Update a Document
.................

.. code:: http

    PUT /api/documents/{id}
    PATCH /api/documents/{id}

* Parameters:

  * all the document fields described in :ref:`rest_general_guide`
  * ``content``: an (optional) content field with the raw XML of the content of the document. ``string``

Updates a document. Use `PUT` when updating all the details of a document. Use `PATCH` when updating only some fields.

If you include the ``content`` parameter, the content of the entire document
will be overwritten. Most other fields of the document, such as the FRBR URI
and the title will be re-read from the new XML, overwriting any existing
fields. The new XML must be valid Akoma Ntoso 2.0 XML.

You can also update the content of the document using ``PUT /api/documents/{id}/content``.


Delete a Document
.................

.. code:: http

    DELETE /api/documents/{id}

Marks the document as deleted. The document can be recovered from the Django Admin area, but will never show up in any API
otherwise.

Create a Document
.................

.. code:: http

    POST /api/documents

* Parameters:

  * all the document fields described in :ref:`rest_general_guide`
  * ``content``: an (optional) content field with the raw XML of the content of the document. ``string``
  * ``file``: an HTTP file attachment (optional). If this is provided, the content of the document is determined from this file.
  * ``file_options..section_number_position``: section number position when ``file`` is given. One of ``before-title``, ``after-title`` or ``guess`` (default). Optional. ``string``
  * ``file_options..cropbox``: crop box for PDF files, as a comma-separated list of integers: ``left, top, width, height``. Optional. ``string``

The ``file`` and ``file_options`` parameters are generally only used when creating a new document. The content of the file will be extracted and parsed. For PDFs, specify a ``cropbox`` to limit content to within the box on each page.

Use `PUT` when updating all the details of a document. Use `PATCH` when updating only some fields.

Get Document Content
....................

.. code:: http

    GET /api/documents/{id}/content

Fetches a JSON description of the raw XML content of a document.

Update Document Content
.......................

.. code:: http

   POST /api/documents/{id}/content

* Parameters:

  * ``content``: raw XML of the document content. ``string``

Updates the content of the entire document. Most other fields of the document, such as the FRBR URI and the title will be re-read
from the new XML, overwriting any existing fields. The new XML must be valid Akoma Ntoso 2.0 XML.

.. warning::
    This overwrites the entire document. Be careful.

* Parameters:

  * ``body``: raw XML of the document body. ``string``

Updates the body of the document. The new XML must be valid Akoma Ntoso 2.0 XML ``<body>`` element.

Attachments
-----------

You can attach arbitrary binary files to documents. Each file has a ``filename`` and ``mime_type``.

.. note::

  Attachments are also made available when embedding images into a document. An attachment with a
  ``filename`` of ``logo.png`` is available at ``<document url>/media/logo.png``.


List Attachments
................

.. code:: http

    GET /api/documents/{id}/attachments

Fetches a JSON description of the attachments to a document.

================= =================================================================================== ==========
Field             Description                                                                         Type      
================= =================================================================================== ==========
id                Unique id of this attachment. Read-only.                                            Integer
created_at        Timestamp of when the attachment was first created. Read-only.                      ISO8601
download_url      URL for downloading this attachment. Read-only.                                     URL
filenmae          Name for this attachment.                                                           String
mime_type         The `mime type <https://en.wikipedia.org/wiki/Media_type>`_ of the attachment.      String
size              Size of the attachment in bytes. Read-only.                                         Integer
updated_at        Timestamp of when the attachment was last updated. Read-only.                       ISO8601
url               URL for fetching details of this attachment. Read-only.                             URL
view_url          URL for viewing the attachment in-line in the browser, if possible. Read-only.      URL
================= =================================================================================== ==========

Create an Attachment
....................

.. code:: http

    POST /api/documents/{id}/attachments

Creates a new attachment. Include a ``file`` multi-part field to upload the binary content.

Update an Attachment
....................

.. code:: http

    PUT /api/documents/{id}/attachments/{id}
    PATCH /api/documents/{id}/attachments/{id}

Update an attachment.

Delete an Attachment
....................

.. code:: http

    DELETE /api/documents/{id}/attachments/{id}

Deletes an attachment.

Helpers
-------

Parse Text into Akoma Ntoso
...........................

.. code:: http

    POST /api/parse

* Parameters:

  * ``file``: an HTTP file attachment (optional). If this is provided, remaining input parameters are ignored. ``file``
  * ``content``: content to convert. ``string``
  * ``fragment``: if this is a fragment, not a whole document, the name of the fragment type. Optional. ``string``
  * ``id_prefix``: prefix to use when generating IDs, especially when parsing a fragment. Optinal. ``string``

Parse plain text into Akoma Ntoso. If a ``file`` is given, then ``content`` is ignored. Otherwise, ``content`` is the text to parse.
If the content is only a fragment of text, not a full document, then specify the fragment type, such as ``sections``, and the
prefix to use when generating IDs.

Render Akoma Ntoso into HTML
............................

.. code:: http

    POST /api/render

* Parameters:

  * ``document``: a document object, included the ``content`` attribute.

Renders a full document into HTML.

Find and Link Defined Terms
...........................

.. code:: http

    POST /api/analysis/link-terms

* Parameters:

  * ``document``: a document description, only the ``content`` element is required

Finds defined terms in a document, and finds references to those terms.

Find and Link Referenced Acts
..............................

.. code:: http

    POST /api/analysis/link-references

* Parameters:

  * ``document``: a document description, including the ``content`` element

Finds and links references to other acts in the document.
