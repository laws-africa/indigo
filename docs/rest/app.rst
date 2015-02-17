.. _rest_app_guide:

Using the Application REST API
==============================

This guide is for developers who want to use the Indigo REST Application API to
manage and edit documents. We assume that you have a basic understanding of web
applications, REST APIs and the `Akoma Ntoso <http://www.akomantoso.org/>`_
standard for legislation (acts).

If you only want to fetch and render published legislation and don't care
about editing legislation, see :ref:`rest_public_guide` instead.

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
-------------

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
