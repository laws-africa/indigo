.. _rest_guide:

Using the REST API
==================

This guide is for developers who want to use the Indigo REST API, either to manage and edit documents
or to fetch and render documents for users to read or download. We assume that
you have a basic understanding of web applications, REST APIs and the
`Akoma Ntoso <http://www.akomantoso.org/>`_ standard for legislation (acts).

The Indigo platform is a Django python web application with three components:

* a web application for managing and editing documents
* an **application REST API** upon which the web application runs
* a **public read-only REST API** for vending legislative documents in HTML and XML

The two APIs are the interesting parts. The main REST API supports the creation, editing
and management of a library of legislative documents. The public read-only API
provides access to published documents in XML, HTML or other formats.

Both APIs share some concepts which we're going to discuss first. Then we'll explore
the two sets in detail individually.

Documents
---------

A **document** is the primary data type in the platform. It represents a single
version of a legislation document such as an act. It contains metadata such as
a title, year of publication, country as well as content in Akoma Ntoso XML.

The Akoma Ntoso standard uses an FRBR URI to uniquely identify an item of legislation. For example, the URI

    ``/za/act/1998/84/``

identifies the `National Forests Act 84 of 1998 <http://www.saflii.org/za/legis/consol_act/nfa1998194/>`_.
The components indicate that the document is from South Africa (``za``), is an
``act`` and is act number ``84`` to be published in ``1998``. These URIs have a standard
format and are well-known and so can be guessed. This is useful when an external
system wants to ask us about an act.

.. seealso::
   For more details on FRBR URIs, see http://www.akomantoso.org/docs/akoma-ntoso-user-documentation/metadata-describes-the-content

Every Indigo document has an FRBR URI associated with it which is used to identify it in the
public REST API. 

Every Indigo document also has a uinque numeric identifier ``id``. This is assigned by
the platform and is unique to that document.

A new document is created each time a new **amendment** must be applied to an
existing document. A single piece of legislation that has been amended over
time is comprised of multiple separate documents, one for each amendment. Each
amended version of the document has a different ``id``, but the same URI.

The **application API** uses the numeric IDs to identify documents so that it can
handle deleted documents, draft documents and amended documents with the same
URI.

The **public API** uses the FRBR URI to identify documents so that anyone can
find a document just by constructing a valid FRBR URI.

Application API
---------------

The application API is the REST API used by the web editor to manage documents. With it you can:

* create new documents
* edit, update and delete existing documents
* list and search for documents
* manage users and passwords

The API is available at

    ``http://indigo.code4sa.org/api/``

and is easy to explore using a browser.

It follows normal REST semantics using HTTP methods such as ``GET``, ``POST``, ``PUT`` and ``DELETE``.

Content types
^^^^^^^^^^^^^

The REST API returns JSON by default. You can explicitly request JSON by including ``Accept: application/json``
as a request header. You can also include ``.json`` at the end of the request URL.

When submitting data to the api, either encode it as JSON and include an appropriate header:

.. code-block:: HTTP

    POST /api HTTP/1.1
    Accept: application/json
    Content-Type: application/json; charset=utf-8
    
    {
        "key": "value"
    }

or use form encoding, also with an appropriate header:

.. code-block:: HTTP

    POST /auth/login/ HTTP/1.1
    Accept: application/json
    Content-Type: application/x-www-form-urlencoded; charset=utf-8
   
    key=value


All our examples will use the JSON format for requests.

Authentication
^^^^^^^^^^^^^^

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

Public API
----------
