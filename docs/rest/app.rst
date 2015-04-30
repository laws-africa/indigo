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

List Documents
--------------

.. code:: http

    GET /api/documents

Lists the documents in the library.

Get a Document
--------------

.. code:: http

    GET /api/documents/{id}

Fetches a JSON description of a document. This does not include the full content or body of the document since those may be very large.

Update a Document
-----------------

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
-----------------

.. code:: http

    DELETE /api/documents/{id}

Marks the document as deleted. The document can be recovered from the Django Admin area, but will never show up in any API
otherwise.

Create a Document
-----------------

.. code:: http

    POST /api/documents

* Parameters:

  * all the document fields described in :ref:`rest_general_guide`
  * ``content``: an (optional) content field with the raw XML of the content of the document. ``string``

Updates a document. Use `PUT` when updating all the details of a document. Use `PATCH` when updating only some fields.

Get Document Content
--------------------

.. code:: http

    GET /api/documents/{id}/content

Fetches a JSON description of the raw XML content of a document.

Update Document Content
-----------------------

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

Convert a Document
------------------

.. code:: http

    POST /api/convert

* Parameters:

  * ``inputformat``: the format of the data in ``content``, required if ``content`` is given. One of: ``text/plain``, ``application/xml``, ``application/json``
  * ``outputformat``: the desired output format. One of: ``application/xml``, ``text/html``, ``text/json``
  * ``file``: an HTTP file attachment (optional). If this is provided, remaining input parameters are ignored. ``file``
  * ``content``: content to convert. ``string``

Converts one type of content into another. This allows you to convert a PDF or Word document
into Akoma Ntoso XML, HTML or plain text.

The content to be converted `from` must be passed in as either a file upload in the ``file`` parameter or in the raw in the ``content`` parameter.
If you use ``content``, you must provide an ``inputformat`` parameter that describes the format of the input. If ``file`` is used, the format is
determined by the mime type of the uploaded file.

The output data depends on the ``outputformat`` parameter. For most outputs, the response is a JSON object with a single ``output``
property.

Not all formats have all the detail necessary to convert to other formats. For instance, plain text doesn't have enough information
to convert to a complete JSON or Akoma Ntoso XML format. In this cases, placeholder values are used (eg. for the FRBR URI, publication time, etc.).
