.. _rest_public_guide:

Using the Public REST API
=========================

This guide is for developers who want to use the Indigo Public REST API
to fetch and render documents for users to read or download. We assume that
you have a basic understanding of web applications, REST APIs and the
`Akoma Ntoso <http://www.akomantoso.org/>`_ standard for legislation (acts).

If you want to manage and edit a collection of legislation see :ref:`rest_app_guide` instead.

Public API
----------

The public API is a read-only API for exploring a collection of legislative documents. Using it, you can:

* get a list of all acts by country and year
* get the raw Akoma Ntoso XML of an act
* get an human-friendly HTML version of an act

The public API relies heavily on FRBR URIs (and URI fragments) for identifying content, be sure to read up on FRBR URIs above.


.. note::

   When we use a URL such as ``/api/frbr-uri/`` in this guide, the ``frbr-uri`` part is a full FRBR URI, such as ``/za/act/1998/84/``.

Content Types
^^^^^^^^^^^^^

Some responses can be returend in multiple formats. You can choose the content
type of a response by including an ``Accept`` header or ``.format`` at the end
of the URL. Not all responses support all formats.

* ``.json``: return JSON
* ``.xml``: return Akoma Ntoso XML
* ``.html``: return human friendly HTML

By default the API returns JSON.

.. seealso::

   For more information on content type negotation see http://www.django-rest-framework.org/api-guide/content-negotiation/


Listing acts
^^^^^^^^^^^^

* ``GET /api/za/``
* ``GET /api/za/act/``
* ``GET /api/za/act/2007/``
  
  * Content types: JSON

These endpoints list all acts for a country or year.  To list the available acts for a country you'll need the `two-letter country code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_ for the country.

Entire act
^^^^^^^^^^

* ``GET /api/frbr-uri/``

  * Content types: JSON, XML, HTML


This returns the entire contents of an act. For example, the HTML version of ``/za/act/1998/84/`` is available at:

    ``http://indigo.code4sa.org/api/za/act/1998/.html``

This might look a bit weird, but it's actually correct since the FRBRI URI ends in a ``/``. If you like, you can also try it without the ``/``

    ``http://indigo.code4sa.org/api/za/act/1998.html``

The raw XML is available at one of:

    ``http://indigo.code4sa.org/api/za/act/1998/.xml``

    ``http://indigo.code4sa.org/api/za/act/1998.xml``


Table of Contents
^^^^^^^^^^^^^^^^^

* ``GET /api/frbr-uri/contents.json``

  * Content types: JSON

Get a descirption of the table of contents of an act.


Using HTML Responses
^^^^^^^^^^^^^^^^^^^^

TODO:

* talk about CSS

