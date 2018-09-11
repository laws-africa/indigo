Indigo Platform
===============

.. image:: logo.png

Indigo is `AfricanLII's <http://africanlii.org/>`_ document management system for managing, capturing and publishing
legislation in the `Akoma Ntoso <http://www.akomantoso.org/>`_ format, built by
`OpenUp <https://openup.org.za>`_ with a grant from `Indigo Trust <http://indigotrust.org.uk/>`_.

You can try it out at `indigo-sandbox.openup.org.za <https://indigo-sandbox.openup.org.za>`_. Login with the username and password `guest@example.com`.

Visit our `GitHub repository <https://github.com/OpenUpSA/indigo>`_ to find out how you
can contribute to the project.

The Indigo platform is a Django python web application with three components:

* a web application for managing and editing documents
* a **read-only REST API** for vending published legislative documents in HTML and XML

The main REST API supports the creation, editing
and management of a library of legislative documents. The public read-only API
provides access to published documents in XML, HTML or other formats.

Contents
--------

.. toctree::
   :maxdepth: 1

   running/index
   running/configuration
   guide/index
   guide/law-intro
   api/public
   changelog

Documents
---------

A **document** is the primary data type in the platform. It represents a single
version of a legislation document such as an act. It contains metadata such as
a title, year of publication, country as well as content in Akoma Ntoso XML.

The Akoma Ntoso standard uses an FRBR URI to uniquely identify an item of legislation. For example, the URI

    ``/za/act/1998/84``

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
