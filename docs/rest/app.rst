.. _rest_app_guide:

Using the Application REST API
==============================

This guide is for developers who want to use the Indigo REST Application API to
manage and edit documents. We assume that you have a basic understanding of web
applications, REST APIs and the `Akoma Ntoso <http://www.akomantoso.org/>`_
standard for legislation (acts).

See :ref:`rest_general_guide` for general API details such as content types and
what the fields of a Document are.

If you only want to fetch and render published legislation and don't care
about editing legislation, see :ref:`rest_public_guide` instead.

Application API
---------------

The application API is the REST API used by the web editor to manage documents. With it you can:

* create new documents
* edit, update and delete existing documents
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
